"""Uma linha por conta (usuarios.csv) com treinos e minutos de atividades.parquet (prompt 06).

Lê só os brutos (SHA-256 antes e depois). Aplica as decisões já registradas: 22 (conta de teste só
marcada), 23 (remove duração <= 0), 24 e 25 (anula distância > 200 km e com gps_ok falso), fuso do
garmin (-3 h, medido na análise 5) e corte de 30/09/2026 em Brasília. Duplicatas app x relógio e tipo
canônico entram como COLUNAS de marcação, sem remover linha. Resume por user_id antes de juntar.
Saídas: dados/processados/contas_treinos.parquet e saidas/granularidade_contas_treinos.md.
"""

import hashlib
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
USUARIOS = RAIZ / "dados" / "brutos" / "usuarios.csv"
ATIVIDADES = RAIZ / "dados" / "brutos" / "atividades.parquet"
DESTINO = RAIZ / "dados" / "processados" / "contas_treinos.parquet"
RELATORIO = RAIZ / "saidas" / "granularidade_contas_treinos.md"
CORTE = pd.Timestamp("2026-09-30 23:59:59")
MAPA = {"run": "corrida", "walk": "caminhada", "ride": "pedal", "strength": "forca"}
LIMIAR_KM = 200
TOL = 5.0


def sha256(*caminhos: Path) -> str:
    h = hashlib.sha256()
    for c in caminhos:
        with open(c, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
    return h.hexdigest()


def n(x) -> str:
    return f"{int(x):,}".replace(",", ".")


def tabela(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    return "\n".join([cab, sep, *("| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False))])


def resumo(t: pd.DataFrame, sufixo: str) -> pd.DataFrame:
    g = t.groupby("user_id").agg(**{
        f"treinos{sufixo}": ("atividade_id", "size"),
        f"minutos{sufixo}": ("duracao_min", "sum"),
        f"distancia_km{sufixo}": ("distancia_km", "sum"),  # soma só dos treinos com valor (NaN não entra)
        f"treinos_com_distancia{sufixo}": ("distancia_km", "count"),
    })
    return g


def main() -> None:
    hash_antes = sha256(USUARIOS, ATIVIDADES)
    log: list[str] = []
    L = log.append
    p = print

    # 1. contagens
    us = pd.read_csv(USUARIOS, dtype=str, keep_default_na=False)
    at = pd.read_parquet(ATIVIDADES, engine="pyarrow")
    at["inicio"] = pd.to_datetime(at["inicio"])
    n_contas, n_treinos0 = len(us), len(at)
    p(f"[1] usuarios: {n(n_contas)} linhas, {n(us['user_id'].nunique())} user_id · atividades: {n(n_treinos0)} linhas, {n(at['user_id'].nunique())} user_id")
    L("# Granularidade: uma linha por conta, com treinos e minutos\n")
    L(f"Gerado por `src/contas_treinos.py`. Só leitura dos brutos (SHA-256 conjunto `{hash_antes[:16]}…` conferido antes e depois). Base: `dados/processados/contas_treinos.parquet` (fora do Git).\n")
    L("## 1. Grão e contagens\n")
    L(tabela(pd.DataFrame([
        ["usuarios.csv", "conta (`user_id`)", n(n_contas), n(us["user_id"].nunique())],
        ["atividades.parquet", "treino (`atividade_id`)", n(n_treinos0), n(at["user_id"].nunique())],
        ["contas_treinos.parquet (saída)", "conta (`user_id`)", "= contas de usuarios.csv", ""],
    ], columns=["arquivo", "uma linha por", "linhas", "user_id únicos"])) + "\n")
    dup_us = int(us["user_id"].duplicated().sum())
    dup_at = int(at["atividade_id"].duplicated().sum())
    L(f"- `user_id` repetido em usuarios.csv: {n(dup_us)}; `atividade_id` repetido em atividades.parquet: {n(dup_at)}.")

    # 2. órfãos
    orfaos_ids = set(at["user_id"]) - set(us["user_id"])
    orfaos_treinos = int(at["user_id"].isin(orfaos_ids).sum())
    sem_treino_contas = len(set(us["user_id"]) - set(at["user_id"]))
    p(f"[2] user_id de atividades fora de usuarios: {n(len(orfaos_ids))} ({n(orfaos_treinos)} treinos) · contas sem nenhum treino bruto: {n(sem_treino_contas)}")
    L(f"- `user_id` de atividades que não existe em usuarios.csv: **{n(len(orfaos_ids))}** ({n(orfaos_treinos)} treinos). Contas sem nenhum treino no bruto: {n(sem_treino_contas)}.\n")

    # 3. contas de teste (decisão 22: só marca)
    us["flag_conta_teste"] = us["email"].str.strip().str.lower().str.endswith("@vitaliza.com.br")
    teste = set(us.loc[us["flag_conta_teste"], "user_id"])
    treinos_teste = int(at["user_id"].isin(teste).sum())
    p(f"[3] contas de teste marcadas: {n(len(teste))} · treinos delas: {n(treinos_teste)} · linhas de usuarios: {n(len(us))} → {n(len(us))} (só marca)")

    # 4. fuso e corte
    at["inicio_brt"] = at["inicio"].where(at["origem"] != "garmin", at["inicio"] - pd.Timedelta(hours=3))
    pos_bruto = int((at["inicio"] > CORTE).sum())
    pos_corrigido = int((at["inicio_brt"] > CORTE).sum())
    p(f"[4] depois do corte: {n(pos_bruto)} com o horário bruto · {n(pos_corrigido)} com o fuso do garmin corrigido")

    # etapas de filtro dos treinos
    etapas = [("0. bruto", len(at))]
    t = at[at["duracao_min"] > 0].copy()
    removidos_dur = len(at) - len(t)
    etapas.append(("1. remove duração ≤ 0 (decisão 23)", len(t)))
    t = t[t["inicio_brt"] <= CORTE].copy()
    removidos_corte = etapas[-1][1] - len(t)
    etapas.append(("2. remove início depois de 30/09/2026 (Brasília)", len(t)))
    p(f"[5] treinos: {n(len(at))} → {n(etapas[1][1])} (−{n(removidos_dur)} duração ≤ 0) → {n(len(t))} (−{n(removidos_corte)} pós-corte)")

    # distâncias (decisões 24 e 25)
    k200 = int((t["distancia_km"] > LIMIAR_KM).sum())
    t.loc[t["distancia_km"] > LIMIAR_KM, "distancia_km"] = pd.NA
    kgps = int((~t["gps_ok"] & t["distancia_km"].notna()).sum())
    t.loc[~t["gps_ok"], "distancia_km"] = pd.NA
    t["distancia_km"] = t["distancia_km"].astype("float64")
    p(f"[6] distâncias anuladas: > {LIMIAR_KM} km {n(k200)} · gps_ok falso {n(kgps)} · linhas {n(len(t))}")

    # tipo canônico (coluna) e duplicatas (marca)
    t["tipo_canonico"] = t["tipo"].map(lambda x: MAPA.get(x, x))
    app = t[t["origem"] == "app"]
    rel = t[t["origem"].isin(["garmin", "apple_health"])]
    c = app.merge(rel, on=["user_id", "tipo_canonico", "duracao_min"], suffixes=("_app", "_rel"))
    c["delta"] = (c["inicio_brt_app"] - c["inicio_brt_rel"]).abs().dt.total_seconds() / 60
    c = c[c["delta"] <= TOL].sort_values("delta")
    n_cand = len(c)
    usados_a: set = set()
    usados_r: set = set()
    pares = []
    for a, r, o in zip(c["atividade_id_app"], c["atividade_id_rel"], c["origem_rel"]):
        if a in usados_a or r in usados_r:
            continue
        usados_a.add(a)
        usados_r.add(r)
        pares.append((a, r, o))
    pares = pd.DataFrame(pares, columns=["atividade_id_app", "atividade_id_rel", "origem_rel"])
    por_origem = pares["origem_rel"].value_counts()
    ok_par = len(pares) == int(por_origem.sum()) and pares["atividade_id_app"].is_unique and pares["atividade_id_rel"].is_unique
    t["duplicata_app_relogio"] = t["atividade_id"].isin(pares["atividade_id_app"])  # a ponta app (a que a decisão 11 removeria)
    t["tem_par_relogio"] = t["atividade_id"].isin(pares["atividade_id_rel"])
    p(f"[7] pares app×relógio: {n(len(pares))} ({dict(por_origem)}) · cada treino em um só par: {'ok' if ok_par else 'ERRO'} · linhas {n(len(t))} → {n(len(t))} (só marca)")

    # 7. resumo por user_id ANTES de juntar, duas versões
    r_todos = resumo(t, "")
    r_sem = resumo(t[~t["duplicata_app_relogio"]], "_sem_dup")
    r = r_todos.join(r_sem, how="outer")
    p(f"[8] resumo por user_id: {n(len(r_todos))} contas com treino (todos) · {n(len(r_sem))} (sem duplicatas) · soma treinos {n(r_todos['treinos'].sum())} / {n(r_sem['treinos_sem_dup'].sum())}")

    # 4/5/6. junção esquerda, um user_id por linha, zeros
    base = us.merge(r, left_on="user_id", right_index=True, how="left", validate="one_to_one")
    ok_linhas = len(base) == n_contas
    ok_unico = base["user_id"].is_unique
    p(f"[9] junção esquerda: {n(n_contas)} → {n(len(base))} linhas {'ok' if ok_linhas else 'ERRO'} · user_id únicos {'ok' if ok_unico else 'ERRO'}")
    cols_zero = [c_ for c_ in r.columns]
    base[cols_zero] = base[cols_zero].fillna(0)
    for c_ in ["treinos", "treinos_sem_dup", "treinos_com_distancia", "treinos_com_distancia_sem_dup"]:
        base[c_] = base[c_].astype("int64")
    base["tem_treino"] = base["treinos"] > 0
    base["tem_treino_sem_dup"] = base["treinos_sem_dup"] > 0
    soma_conta = int(base["treinos"].sum())
    ok_soma = soma_conta == len(t)
    ok_soma_sem = int(base["treinos_sem_dup"].sum()) == int((~t["duplicata_app_relogio"]).sum())
    orf_final = int((~t["user_id"].isin(set(us["user_id"]))).sum())
    p(f"[10] soma dos treinos por conta {n(soma_conta)} = treinos usados {n(len(t))} {'ok' if ok_soma else 'ERRO'} · treinos de user_id fora de usuarios: {n(orf_final)}")

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    base.to_parquet(DESTINO, index=False)

    # tabela do item 8: contas, com treino, sem treino em 5 cenários
    def cenario(treinos: pd.DataFrame, sem_teste: bool) -> list:
        cont = us[~us["flag_conta_teste"]] if sem_teste else us
        ids = set(cont["user_id"])
        com = len(set(treinos["user_id"]) & ids)
        return [n(len(cont)), n(com), n(len(cont) - com)]

    em_bruto = at
    sem_pos = at[at["inicio_brt"] <= CORTE]
    final = t
    tab = pd.DataFrame({
        "cenário": ["tudo (bruto)", "sem contas de teste", "sem treinos após o corte", "sem os dois", "base final (+ decisão 23)"],
        "treinos": [n(len(em_bruto)), n((~at['user_id'].isin(teste)).sum()), n(len(sem_pos)),
                    n((~sem_pos['user_id'].isin(teste)).sum()), n((~t['user_id'].isin(teste)).sum())],
    })
    vals = [cenario(em_bruto, False), cenario(em_bruto, True), cenario(sem_pos, False), cenario(sem_pos, True), cenario(final, True)]
    tab["contas"] = [v[0] for v in vals]
    tab["com treino"] = [v[1] for v in vals]
    tab["sem treino"] = [v[2] for v in vals]
    tab = tab[["cenário", "contas", "com treino", "sem treino", "treinos"]]
    p("[11] tabela do item 8 calculada (5 cenários)")

    # efeito das duas versões
    dif_t = int(base["treinos"].sum() - base["treinos_sem_dup"].sum())
    dif_m = base["minutos"].sum() - base["minutos_sem_dup"].sum()
    muda_tem = int((base["tem_treino"] & ~base["tem_treino_sem_dup"]).sum())
    contas_afetadas = int((base["treinos"] != base["treinos_sem_dup"]).sum())
    base_sem_teste = base[~base["flag_conta_teste"]]
    p(f"[12] efeito da duplicata: −{n(dif_t)} treinos ({100*dif_t/base['treinos'].sum():.2f}%) · {n(contas_afetadas)} contas afetadas · {n(muda_tem)} contas passam a sem treino")

    L("## 2. Etapas de filtro dos treinos (linhas antes e depois)\n")
    ef = [["0. bruto", n(len(at)), ""],
          ["1. remove duração ≤ 0 (decisão 23)", n(etapas[1][1]), f"−{n(removidos_dur)}"],
          ["2. remove início depois de 30/09/2026, horário de Brasília", n(len(t)), f"−{n(removidos_corte)}"]]
    L(tabela(pd.DataFrame(ef, columns=["etapa", "treinos", "removidos"])) + "\n")
    L(f"- Fuso: o `inicio` do garmin é UTC (+3 h medido na análise 5); Brasília = garmin − 3 h. Depois do corte: **{n(pos_bruto)}** treinos com o horário bruto, **{n(pos_corrigido)}** com o fuso corrigido (os garmin das primeiras horas de 01/10 voltam para dentro).")
    L(f"- Distância anulada (decisões 24 e 25): {n(k200)} acima de {LIMIAR_KM} km e {n(kgps)} com `gps_ok` falso; as linhas não mudam.")
    L(f"- Treinos de contas de teste no bruto: {n(treinos_teste)} (as contas ficam marcadas, decisão 22).\n")
    L("## 3. Duplicatas app × relógio (só marcadas, nada removido)\n")
    L(f"- Pares (mesma conta, tipo canônico, duração, início ≤ {TOL:g} min com fuso corrigido, um por treino): **{n(len(pares))}** = " +
      " + ".join(f"{n(v)} app com {k}" for k, v in por_origem.items()) + f" {'✔' if ok_par else '✘'}. Candidatos antes do desempate: {n(n_cand)}.")
    L(f"- `duplicata_app_relogio` marca a ponta app ({n(int(t['duplicata_app_relogio'].sum()))} treinos), a que a decisão 11 removeria; a ponta do relógio fica sem marca. `tipo_canonico` é uma coluna nova; o `tipo` original não mudou.\n")
    L("## 4. Resumo por conta e junção\n")
    L(f"- Resumo por `user_id` antes de juntar: {n(len(r_todos))} contas com treino (todos os treinos) e {n(len(r_sem))} (sem as duplicatas).")
    L(f"- Junção esquerda: usuarios.csv {n(n_contas)} → {n(len(base))} linhas {'✔' if ok_linhas else '✘'}; `user_id` repetido: {n(int(base['user_id'].duplicated().sum()))} {'✔' if ok_unico else '✘'}.")
    L(f"- Soma dos treinos por conta: **{n(soma_conta)}** = treinos usados {n(len(t))} {'✔' if ok_soma else '✘'} (sem duplicatas: {n(int(base['treinos_sem_dup'].sum()))} = {n(int((~t['duplicata_app_relogio']).sum()))} {'✔' if ok_soma_sem else '✘'}).")
    L(f"- Treinos de `user_id` ausentes em usuarios.csv: {n(orf_final)}.")
    L("- Contas sem treino ficam com `treinos = 0`, `minutos = 0`, `distancia_km = 0` e `tem_treino = False` (`distancia_km` 0 também vale para quem treinou sem GPS: a soma é só dos treinos com valor).\n")
    L("## 5. Contas e treinos em cada cenário (item 8)\n")
    L(tabela(tab) + "\n")
    L("Cenários com treinos sobre o bruto (sem decisão 23) mostram só o efeito de contas de teste e do corte; a última linha é a base final.\n")
    L("## 6. Tamanho do efeito das duplicatas (todos × sem duplicatas)\n")
    L(tabela(pd.DataFrame([
        ["treinos", n(base["treinos"].sum()), n(base["treinos_sem_dup"].sum()), f"−{n(dif_t)} ({100*dif_t/base['treinos'].sum():.2f}%)"],
        ["minutos", n(base["minutos"].sum()), n(base["minutos_sem_dup"].sum()), f"−{n(dif_m)} ({100*dif_m/base['minutos'].sum():.2f}%)"],
        ["distância (km)", n(base["distancia_km"].sum()), n(base["distancia_km_sem_dup"].sum()),
         f"−{n(base['distancia_km'].sum() - base['distancia_km_sem_dup'].sum())}"],
        ["contas com treino", n(base["tem_treino"].sum()), n(base["tem_treino_sem_dup"].sum()), f"−{n(muda_tem)}"],
        ["contas com número de treinos diferente", "", "", n(contas_afetadas)],
    ], columns=["medida", "todos os treinos", "sem duplicatas", "diferença"])) + "\n")
    L("## 7. Decisões novas propostas (formato do `decisoes.md`, não gravadas)\n")
    L("| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |")
    L("|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|")
    L(f"| 28 | 09/11/2026 | usuarios.csv + atividades.parquet | granularidade: contas (1 linha por conta) × treinos (1 linha por treino) | resumir os treinos por `user_id` e juntar pela esquerda em `contas_treinos.parquet`; contas sem treino ficam com 0 e `tem_treino = False` | juntar direto multiplicaria contas por treino; quem não treinou é informação, não ausência | {n(n_contas)} → {n(len(base))} linhas; {n(int(base['tem_treino'].sum()))} contas com treino e {n(int((~base['tem_treino']).sum()))} sem |")
    L(f"| 29 | 09/11/2026 | atividades.parquet | {n(pos_corrigido)} treinos depois de 30/09/2026 em Brasília ({n(pos_bruto)} com o horário bruto do garmin) | remover da base de contas (corte), com o garmin convertido (−3 h) antes de comparar | nenhuma análise usa informação posterior ao corte; sem o fuso, treinos garmin das primeiras horas de 01/10 ficariam de fora do corte por engano | {n(etapas[1][1])} → {n(len(t))} (−{n(removidos_corte)}) |")
    L(f"| 30 | 09/11/2026 | atividades.parquet | {n(len(pares))} treinos em dobro (app × relógio) | marcar `duplicata_app_relogio` na ponta app em `contas_treinos.parquet`; duas versões de treinos e minutos (`treinos`/`treinos_sem_dup`), sem remover linha | pedido do usuário de ver o tamanho do efeito antes de aplicar a decisão 11 nesta base; as colunas principais usam todos os treinos | {n(len(t))} → {n(len(t))}; efeito −{n(dif_t)} treinos ({100*dif_t/base['treinos'].sum():.2f}%) |")
    estado = "inalterados" if sha256(USUARIOS, ATIVIDADES) == hash_antes else "ALTERADOS"
    L(f"\n---\nConferência: brutos {estado}.")
    RELATORIO.write_text("\n".join(log), encoding="utf-8")
    p(f"brutos {estado} · saída: {DESTINO.relative_to(RAIZ)} ({n(len(base))} linhas, {len(base.columns)} colunas) · {RELATORIO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
