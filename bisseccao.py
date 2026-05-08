"""
Método da Bissecção - Cálculo Numérico
Encontra raízes de f(x) = 0 em um intervalo [a, b]
"""

# Allow user-provided function in user_func.py. If present, use it; otherwise
# fall back to the default polynomial below. This keeps bisseccao.py free of
# non-standard dependencies while letting the UI provide custom equations.
try:
    from user_func import f as _user_f  # type: ignore
except Exception:
    _user_f = None


def f(x):
    """Compute f(x). If user provided a function in user_func.py use it.

    The user function file (user_func.py) should define a function `f(x)` that
    returns a numeric value. It may optionally `import math` if needed.
    """
    if _user_f is not None:
        try:
            return _user_f(x)
        except Exception:
            # If the user function fails for some x, fall back to default.
            pass

    # Default function (used when no user function is present):
    return x**4 - x - 2  # <- DEFAULT (you may override via the UI)


def bisseccao(a, b, tol=1e-6, max_iter=100):
    """
    Método da Bissecção para encontrar raízes de f(x) = 0.

    Parâmetros:
        a       : limite inferior do intervalo
        b       : limite superior do intervalo
        tol     : tolerância (critério de parada), padrão 1e-6
        max_iter: número máximo de iterações, padrão 100

    Retorna:
        raiz    : valor aproximado da raiz
        iteracoes: lista com o histórico de cada iteração
    """

    # Verificação inicial: f(a) e f(b) devem ter sinais opostos
    if f(a) * f(b) >= 0:
        raise ValueError(
            f"f(a) e f(b) precisam ter sinais opostos!\n"
            f"f({a}) = {f(a):.6f}, f({b}) = {f(b):.6f}"
        )

    iteracoes = []
    n = 0

    print("=" * 70)
    print(f"{'Iter':>4} | {'a':>12} | {'b':>12} | {'x_m':>12} | {'f(x_m)':>12} | {'Erro':>12}")
    print("=" * 70)

    while n < max_iter:
        # Calcula o ponto médio
        xm = (a + b) / 2
        fxm = f(xm)
        erro = abs(b - a) / 2

        # Registra a iteração
        iteracoes.append({
            "iter": n + 1,
            "a": a,
            "b": b,
            "xm": xm,
            "fxm": fxm,
            "erro": erro
        })

        print(f"{n+1:>4} | {a:>12.6f} | {b:>12.6f} | {xm:>12.6f} | {fxm:>12.6f} | {erro:>12.8f}")

        # Critério de parada: tolerância atingida ou raiz exata encontrada
        if erro < tol or fxm == 0:
            break

        # Atualiza o intervalo
        if f(a) * fxm < 0:
            b = xm  # raiz está em [a, xm]
        else:
            a = xm  # raiz está em [xm, b]

        n += 1

    print("=" * 70)

    return xm, iteracoes


def main():
    # -----------------------------------------------
    # CONFIGURE OS PARÂMETROS AQUI
    a = 1.0       # Limite inferior do intervalo
    b = 2.0       # Limite superior do intervalo
    tol = 1e-6    # Tolerância desejada
    max_iter = 50 # Máximo de iterações
    # -----------------------------------------------

    # Use apenas caracteres ASCII para compatibilidade com consoles
    print("\n+----------------------------------+")
    print("|     METODO DA BISSECCAO         |")
    print("+----------------------------------+\n")
    # Use apenas ASCII nas mensagens para evitar erros em terminais antigos
    print("Funcao   : f(x) = x^4 - x - 2")
    print(f"Intervalo: [{a}, {b}]")
    print(f"Tolerância: {tol}")
    print(f"Máx. iterações: {max_iter}\n")

    try:
        raiz, historico = bisseccao(a, b, tol, max_iter)

        print(f"\nRaiz encontrada : x approx {raiz:.8f}")
        print(f"f(raiz)         : {f(raiz):.2e}")
        print(f"Iterações       : {len(historico)}")
        print(f"Erro estimado   : {abs(b - a) / 2:.2e}")

    except ValueError as e:
        print(f"\nERRO: {e}")


if __name__ == "__main__":
    main()
