"""Passo 5 da prática 12 · Teste da 3ª variável no gap saiu × ficou.

Pergunta: o gap de engajamento entre quem saiu e quem ficou (comportamento_usuarios.py)
sobrevive quando controlamos por plano, tempo de casa e canal — ou era composição?

Lê dados/processados/comportamento_ate_30jun.parquet (gerado por
src/comportamento_usuarios.py). Saída: saidas/terceira_variavel.md.
"""

import pandas as pd

from utils import PROCESSADOS, SAIDAS, mostrar

REF = pd.Timestamp("2026-06-30")


def fmt(n) -> str:
    return f"{n:,}".replace(",", ".")


def gap_por(t: pd.DataFrame, dim: str, feat: str) -> pd.DataFrame:
    g = t.groupby([dim, "grupo"], observed=True)[feat].median().unstack()
    g["gap"] = g["saiu"] - g["ficou"]
    return g.round(1)


def main() -> None:
    t = pd.read_parquet(PROCESSADOS / "comportamento_ate_30jun.parquet")
    mostrar("base por usuário lida", t)
    t["inicio"] = pd.to_datetime(t["inicio"])
    t["faixa_casa"] = pd.cut((REF - t["inicio"]).dt.days / 30.44,
                             [0, 6, 12, 24, 999], labels=["até 6m", "6–12m", "1–2a", "2a+"])

    churn = lambda dim: (t.groupby(dim, observed=True)
                          .agg(n=("user_id", "size"),
                               churn_pct=("grupo", lambda s: round(100 * (s == "saiu").mean(), 1))))

    c_plano, c_casa, c_canal = churn("plano_atual"), churn("faixa_casa"), churn("canal_cobranca")
    g_plano = gap_por(t, "plano_atual", "treinos_jan_jun")
    g_casa = gap_por(t, "faixa_casa", "treinos_jan_jun")
    g_sessoes = gap_por(t, "plano_atual", "sessoes_app_mes")

    for rotulo, tab in [("churn por plano", c_plano), ("churn por tempo de casa", c_casa),
                        ("churn por canal", c_canal),
                        ("gap de treinos jan–jun por plano", g_plano),
                        ("gap de treinos jan–jun por tempo de casa", g_casa),
                        ("gap de sessões/mês por plano", g_sessoes)]:
        print(f"\n=== {rotulo} ===\n{tab.to_string()}")

    md = lambda df: df.to_markdown()
    (SAIDAS / "terceira_variavel.md").write_text("\n".join([
        "# Teste da 3ª variável — saiu × ficou (passo 5 da prática 12)",
        "",
        "Gerado por `src/terceira_variavel.py` a partir de `comportamento_ate_30jun.parquet` "
        f"({fmt(len(t))} pagantes ativos em 30/06; tudo medido até 30/06).",
        "",
        "## Churn do trimestre por recorte",
        "", "### Plano", "", md(c_plano),
        "", "### Tempo de casa em 30/06", "", md(c_casa),
        "", "### Canal de cobrança", "", md(c_canal),
        "",
        "## O gap de engajamento sobrevive ao controle?",
        "",
        "Mediana de treinos jan–jun (saiu × ficou) **dentro de cada plano**:",
        "", md(g_plano),
        "",
        "Dentro de cada **faixa de tempo de casa**:",
        "", md(g_casa),
        "",
        "Sessões no app/mês dentro de cada plano:",
        "", md(g_sessoes),
        "",
        "## Leitura",
        "",
        "1. **Plano é a 3ª variável mais forte do churn**: mensal sai a 24,7%, anual a 10,9% "
        "(e o grupo que saiu é 62% mensal; o que ficou, 62% anual).",
        "2. **Mas o gap de engajamento NÃO é só composição** — ele sobrevive ao controle e muda "
        "de cara: no plano **anual**, quem saiu treinou 9 contra 42 de quem ficou (gap −33) — "
        "abandono de uso meses antes de deixar a assinatura expirar. No **mensal**, o gap é "
        "pequeno (40 × 47): o churner mensal ainda treinava quase como quem ficou.",
        "3. **Tempo de casa**: o churn concentra-se em 6–12 meses (25,0%) — a janela da primeira "
        "renovação anual — e cai com a antiguidade (2a+: 8,9%). Entre novatos (até 6m) o gap de "
        "treino é quase nulo (−2); entre veteranos que saem, é enorme (−33).",
        "4. **Implicação**: engajamento em queda é um ótimo preditor para o churn do plano anual "
        "(dá tempo de agir antes da renovação), mas fraco para o mensal — onde a saída deve ter "
        "outros motores (preço, cobrança/recusas, concorrência). A régua de retenção não pode "
        "ser uma só.",
        "",
        "As 3 frases finais (diz / não diz / próxima pergunta) ficam para a discussão em grupo.",
    ]) + "\n", encoding="utf-8")
    print(f"\n[saída] {SAIDAS / 'terceira_variavel.md'}")


if __name__ == "__main__":
    main()
