from __future__ import annotations

# Taxas por token (USD). Fonte única de verdade para estimativa de custo.
# Modelo: deepseek-v4-flash (15/75 por milhão de tokens)
RATE_IN_PER_MILLION = 15
RATE_OUT_PER_MILLION = 75


def estimate_cost(tokens_in: int, tokens_out: int) -> float:
    """Estima custo em USD baseado nos tokens de input e output.

    Args:
        tokens_in: Total de tokens de entrada (prompt + contexto)
        tokens_out: Total de tokens de saída (gerados pelo modelo)

    Returns:
        Custo estimado em dólares, com 4 casas decimais.
    """
    return (tokens_in * RATE_IN_PER_MILLION + tokens_out * RATE_OUT_PER_MILLION) / 1_000_000
