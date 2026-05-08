"""
Gera um grafico da funcao f(x) e marca os pontos xm das iteracoes do metodo da bisseccao.

Uso:
  python plot_bisseccao.py

O script tenta usar matplotlib; se nao estiver disponivel, gera um arquivo SVG
chamado 'bisseccao_plot.svg'. O historico de iteracoes e a raiz sao obtidos
executando a funcao bisseccao definida no modulo bisseccao.py.
"""

import importlib
import os
import sys
import webbrowser

try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    HAS_MPL = False


def main():
    # Importa o modulo que contem f e o metodo bisseccao
    try:
        mod = importlib.import_module('bisseccao')
    except Exception as e:
        print('Erro ao importar o modulo bisseccao:', e)
        sys.exit(1)

    # Parametros usados na execucao (mesmos do exemplo)
    a0 = 1.0
    b0 = 2.0
    tol = 1e-6
    max_iter = 50

    # Executa o metodo e obtem historico
    raiz, historico = mod.bisseccao(a0, b0, tol, max_iter)

    # Pontos para desenhar a curva
    n_points = 800
    xs = [a0 + i * (b0 - a0) / n_points for i in range(n_points + 1)]
    ys = [mod.f(x) for x in xs]

    # limites em y com margem
    ymin = min(ys)
    ymax = max(ys)
    yrange = ymax - ymin if ymax != ymin else abs(ymax) + 1.0
    pad = 0.12 * yrange
    ymin -= pad
    ymax += pad

    if HAS_MPL:
        # Plota usando matplotlib
        plt.figure(figsize=(9, 5.5))
        plt.plot(xs, ys, label='f(x) = x^3 - x - 2', color='tab:blue')
        plt.axhline(0, color='black', linewidth=0.8)

        # marca os xm de cada iteracao e anota alguns indices
        xm_list = [it['xm'] for it in historico]
        fxm_list = [it['fxm'] for it in historico]
        import matplotlib.cm as cm
        cmap = cm.get_cmap('viridis')
        for i, (xmi, fmi) in enumerate(zip(xm_list, fxm_list), start=1):
            c = cmap(i / max(1, len(xm_list)))
            plt.scatter(xmi, fmi, color=c, s=28, edgecolor='black')
            if i % 5 == 0 or i == len(xm_list):
                plt.annotate(str(i), xy=(xmi, fmi), xytext=(4, 4), textcoords='offset points', fontsize=8)

        # linhas verticais mostrando o ultimo intervalo
        if historico:
            last = historico[-1]
            plt.axvline(last['a'], color='gray', linestyle='--', alpha=0.6)
            plt.axvline(last['b'], color='gray', linestyle='--', alpha=0.6)

        # marca a raiz final
        plt.scatter(raiz, mod.f(raiz), color='red', s=70, label=f'raiz approx {raiz:.8f}')

        # legenda customizada (proxy artists) para incluir todos os elementos
        try:
            from matplotlib.lines import Line2D
            curve_handle = Line2D([0], [0], color='tab:blue', lw=1.6)
            xm_handle = Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markeredgecolor='black', markersize=6)
            root_handle = Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markeredgecolor='black', markersize=9)
            y0_handle = Line2D([0], [0], color='black', lw=0.8)
            interval_handle = Line2D([0], [0], linestyle='--', color='gray')

            plt.legend(handles=[curve_handle, xm_handle, root_handle, y0_handle, interval_handle],
                       labels=['f(x) = x^3 - x - 2', 'xm (iterações)', f'raiz approx {raiz:.8f}', 'y = 0', 'intervalo final'],
                       loc='best')
        except Exception:
            plt.legend()

        # mostra a formula no canto superior esquerdo
        plt.gca().text(0.02, 0.97, 'f(x) = x^3 - x - 2', transform=plt.gca().transAxes, fontsize=10, verticalalignment='top')

        plt.title('Metodo da Bisseccao - f(x) = x^3 - x - 2')
        plt.xlabel('x')
        plt.ylabel('f(x)')
        plt.ylim(ymin, ymax)
        plt.grid(alpha=0.25)
        fname = 'bisseccao_plot.png'
        plt.tight_layout()
        plt.savefig(fname, dpi=150)
        print('Grafico salvo em:', fname)

        # gerar um zoom detalhado em torno da raiz
        try:
            last = historico[-1] if historico else {'a': a0, 'b': b0}
            center = raiz
            delta = max((last['b'] - last['a']) * 10.0, 0.02)
            zmin = max(a0, center - delta)
            zmax = min(b0, center + delta)
            xs_z = [zmin + i * (zmax - zmin) / 600 for i in range(601)]
            ys_z = [mod.f(x) for x in xs_z]

            plt.figure(figsize=(6, 4))
            plt.plot(xs_z, ys_z, color='tab:blue', label='f(x)')
            plt.axhline(0, color='black', linewidth=0.8, label='y = 0')
            # marcar os xm que caem no zoom
            for i, it in enumerate(historico, start=1):
                if zmin <= it['xm'] <= zmax:
                    plt.scatter(it['xm'], it['fxm'], color='red', s=40, edgecolor='black')
                    plt.annotate(str(i), xy=(it['xm'], it['fxm']), xytext=(4, 4), textcoords='offset points', fontsize=8)

            plt.gca().text(0.02, 0.97, 'f(x) = x^3 - x - 2', transform=plt.gca().transAxes, fontsize=9, verticalalignment='top')
            plt.title('Zoom na raiz - Metodo da Bisseccao')
            plt.xlabel('x')
            plt.ylabel('f(x)')
            plt.grid(alpha=0.25)
            plt.legend()
            fname_z = 'bisseccao_plot_zoom.png'
            plt.tight_layout()
            plt.savefig(fname_z, dpi=150)
            print('Zoom salvo em:', fname_z)
            try:
                if sys.platform.startswith('win'):
                    os.startfile(fname_z)
                else:
                    webbrowser.open('file://' + os.path.realpath(fname_z))
            except Exception:
                pass
        except Exception:
            # não crítico, continua
            pass

    else:
        # Fallback: gerar um SVG simples sem bibliotecas externas
        width, height = 900, 500
        left_pad, right_pad, top_pad, bottom_pad = 60, 20, 20, 60

        def x2px(x):
            return left_pad + (x - a0) / (b0 - a0) * (width - left_pad - right_pad)

        def y2px(y):
            return top_pad + (ymax - y) / (ymax - ymin) * (height - top_pad - bottom_pad)

        points = [f"{x2px(x):.2f},{y2px(y):.2f}" for x, y in zip(xs, ys)]

        svg_path = 'bisseccao_plot.svg'
        svg_zoom_path = 'bisseccao_plot_zoom.svg'

        # helper para gerar cores interpoladas
        def lerp_color(c1, c2, t):
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            return f'#{r:02x}{g:02x}{b:02x}'

        start_col = (255, 99, 71)   # tomato-like
        end_col = (30, 144, 255)    # dodgerblue

        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n')
            f.write('<rect width="100%" height="100%" fill="white"/>\n')
            f.write(f'<!-- eixo x em y=0 -->\n')
            f.write(f'<line x1="{left_pad}" y1="{y2px(0):.2f}" x2="{width-right_pad}" y2="{y2px(0):.2f}" stroke="black" stroke-width="1"/>\n')
            # curva
            f.write(f'<polyline fill="none" stroke="blue" stroke-width="1.5" points="{" ".join(points)}" />\n')

            # desenha linhas dos intervalos (sombreamento leve)
            for i, it in enumerate(historico, start=1):
                t = (i-1) / max(1, len(historico)-1)
                col = lerp_color(start_col, end_col, t)
                ax = x2px(it['a'])
                bx = x2px(it['b'])
                f.write(f'<rect x="{ax:.2f}" y="{top_pad:.2f}" width="{(bx-ax):.2f}" height="{(height-top_pad-bottom_pad):.2f}" fill="{col}" fill-opacity="0.04" stroke="none"/>\n')

            # pontos xm e anotacoes
            for i, it in enumerate(historico, start=1):
                cx = x2px(it['xm'])
                cy = y2px(it['fxm'])
                t = (i-1) / max(1, len(historico)-1)
                col = lerp_color(start_col, end_col, t)
                f.write(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="4" fill="{col}" stroke="black" stroke-width="0.6"/>\n')
                # anotar todos com pequenas etiquetas
                f.write(f'<text x="{cx+6:.1f}" y="{cy-6:.1f}" font-size="10" fill="#222">{i}</text>\n')

            # linhas do ultimo intervalo (destaque)
            if historico:
                last = historico[-1]
                f.write(f'<line x1="{x2px(last["a"]):.2f}" y1="{top_pad}" x2="{x2px(last["a"]):.2f}" y2="{height-bottom_pad}" stroke="gray" stroke-dasharray="4" stroke-width="1.2"/>\n')
                f.write(f'<line x1="{x2px(last["b"]):.2f}" y1="{top_pad}" x2="{x2px(last["b"]):.2f}" y2="{height-bottom_pad}" stroke="gray" stroke-dasharray="4" stroke-width="1.2"/>\n')

            # legenda manual no canto superior direito
            lg_x = width - right_pad - 220
            lg_y = top_pad + 6
            f.write(f'<rect x="{lg_x}" y="{lg_y}" width="210" height="92" fill="#fff" stroke="#ddd" stroke-width="0.8"/>\n')
            f.write(f'<text x="{lg_x+8}" y="{lg_y+18}" font-size="12" fill="#111">Legenda:</text>\n')
            f.write(f'<circle cx="{lg_x+16}" cy="{lg_y+34}" r="6" fill="#1e90ff" stroke="#000" stroke-width="0.4"/>\n')
            f.write(f'<text x="{lg_x+32}" y="{lg_y+38}" font-size="11">f(x) = x^3 - x - 2</text>\n')
            f.write(f'<circle cx="{lg_x+16}" cy="{lg_y+54}" r="5" fill="#ff6347" stroke="#000" stroke-width="0.4"/>\n')
            f.write(f'<text x="{lg_x+32}" y="{lg_y+58}" font-size="11">xm (iterações)</text>\n')
            f.write(f'<rect x="{lg_x+10}" y="{lg_y+64}" width="12" height="8" fill="#ddd" stroke="#000"/>\n')
            f.write(f'<text x="{lg_x+32}" y="{lg_y+74}" font-size="11">intervalo (sombreamento)</text>\n')

            f.write(f'<text x="{left_pad}" y="{height-10}" font-size="12">raiz approx {raiz:.8f}  f(raiz)={mod.f(raiz):.2e}</text>\n')
            # mostrar formula no canto superior esquerdo
            f.write(f'<text x="{left_pad}" y="{top_pad-4}" font-size="12">f(x) = x^3 - x - 2</text>\n')
            f.write('</svg>\n')

        # gerar SVG zoom detalhado
        if historico:
            last = historico[-1]
            center = raiz
            delta = max((last['b'] - last['a']) * 10.0, 0.02)
            zmin = max(a0, center - delta)
            zmax = min(b0, center + delta)
        else:
            zmin, zmax = a0, b0

        # gerar pontos para o zoom
        n_zoom = 600
        xs_z = [zmin + i * (zmax - zmin) / n_zoom for i in range(n_zoom + 1)]
        ys_z = [mod.f(x) for x in xs_z]

        def x2px_z(x, w=700, h=380, lp=50, rp=20, tp=20, bp=50):
            return lp + (x - zmin) / (zmax - zmin) * (w - lp - rp)

        def y2px_z(y, w=700, h=380, lp=50, rp=20, tp=20, bp=50):
            ymin_z = min(ys_z)
            ymax_z = max(ys_z)
            return tp + (ymax_z - y) / (ymax_z - ymin_z if ymax_z != ymin_z else 1.0) * (h - tp - bp)

        with open(svg_zoom_path, 'w', encoding='utf-8') as fz:
            w, h, lp, rp, tp, bp = 700, 380, 50, 20, 20, 50
            fz.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n')
            fz.write('<rect width="100%" height="100%" fill="white"/>\n')
            # curva zoom
            pts_z = [f"{x2px_z(x,w,h,lp,rp,tp,bp):.2f},{y2px_z(y,w,h,lp,rp,tp,bp):.2f}" for x, y in zip(xs_z, ys_z)]
            fz.write(f'<polyline fill="none" stroke="blue" stroke-width="1.6" points="{" ".join(pts_z)}" />\n')

            # pontos xm no zoom
            for i, it in enumerate(historico, start=1):
                if zmin <= it['xm'] <= zmax:
                    cx = x2px_z(it['xm'], w, h, lp, rp, tp, bp)
                    cy = y2px_z(it['fxm'], w, h, lp, rp, tp, bp)
                    t = (i-1) / max(1, len(historico)-1)
                    col = lerp_color(start_col, end_col, t)
                    fz.write(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="5" fill="{col}" stroke="#111" stroke-width="0.8"/>\n')
                    fz.write(f'<text x="{cx+6:.1f}" y="{cy-6:.1f}" font-size="11">{i}</text>\n')

            fz.write(f'<text x="{lp}" y="{h-12}" font-size="12">zoom: [{zmin:.8f}, {zmax:.8f}]  raiz approx {raiz:.8f}</text>\n')
            fz.write('</svg>\n')

        print('Matplotlib nao encontrado - graficos SVG salvos em:', svg_path, 'e', svg_zoom_path)
        try:
            webbrowser.open('file://' + os.path.realpath(svg_path))
        except Exception:
            pass


if __name__ == '__main__':
    main()
