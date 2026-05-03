import sys
import numpy as np
import pandas as pd
from scipy import stats
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QSplitter, QFrame
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from model import modelo

####parte visual da app

### Já define as cores para utilizar
DARK   = "#1a1f2e"
PANEL  = "#232a3b"
GRID   = "#545e6f"
TEXT   = "#cdd8f0"
GREEN  = "#4caf50"
BLUE   = "#42a5f5"
ORANGE = "#ffa726"
RED    = "#ef5350"
 
STYLE = """
QWidget {
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    background-color: #1a1f2e;
    color: #e0e6f0;
}
QPushButton {
    background-color: #2e7d32;
    color: white;
    padding: 7px 14px;
    border-radius: 6px;
    font-weight: bold;
}
QPushButton:hover { background-color: #1b5e20; }
QLabel#titulo {
    font-size: 15px;
    font-weight: bold;
    color: #cdd8f0;
    padding: 4px 0;
}
QTableWidget {
    background-color: #232a3b;
    gridline-color: #2e3a50;
    border: 1px solid #2e3a50;
    border-radius: 4px;
    color: #cdd8f0;
}
QHeaderView::section {
    background-color: #2c3e55;
    color: #cdd8f0;
    font-weight: bold;
    padding: 4px;
    border: none;
}
QScrollArea { border: none; }
QFrame#card {
    background-color: #232a3b;
    border: 1px solid #2e3a50;
    border-radius: 8px;
}
"""
 
 
def style_ax(ax, title):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.set_title(title, color=TEXT, fontsize=10, fontweight="bold", pad=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.grid(True, color=GRID, linewidth=0.5, linestyle="--", alpha=0.6)
 
 
##### elementos
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MPTropic")  ### nome no começo da janela
        self.setGeometry(100, 80, 1440, 860)
        self.df = None
        self._build_ui()
        self.setStyleSheet(STYLE)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        top = QHBoxLayout()                   
        self.label = QLabel("Carregue seus dados (.csv ou .xlsx)")
        self.label.setObjectName("titulo")
        top.addWidget(self.label)
        top.addStretch()

        self.btn_load = QPushButton("📂 Carregar Arquivo")
        self.btn_load.clicked.connect(self.carregar_arquivo)
        top.addWidget(self.btn_load)

        self.btn_export = QPushButton("💾 Exportar Resultado")
        self.btn_export.clicked.connect(self.exportar_resultado)
        top.addWidget(self.btn_export)
        root.addLayout(top)

        #Splitter principal
        splitter = QSplitter(Qt.Horizontal)

        # Painel esquerdo
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(8)

        lbl_eq = QLabel("📑 Equação: y = 0,0673 · (ρ · DAP² · H)^0,976")
        lbl_eq.setObjectName("titulo")
        left_layout.addWidget(lbl_eq)

        lbl_stat = QLabel("Estatística")
        lbl_stat.setObjectName("titulo")
        left_layout.addWidget(lbl_stat)

        self.stat_table = QTableWidget()
        self.stat_table.setMinimumHeight(210)
        left_layout.addWidget(self.stat_table)

        lbl_anova = QLabel("Teste Anova (DAP, H, ρ, y)")
        lbl_anova.setObjectName("titulo")
        left_layout.addWidget(lbl_anova)

        self.anova_table = QTableWidget()
        self.anova_table.setMinimumHeight(110)
        left_layout.addWidget(self.anova_table)

        lbl_dados = QLabel("Dados Carregados")
        lbl_dados.setObjectName("titulo")
        left_layout.addWidget(lbl_dados)

        self.table = QTableWidget()
        left_layout.addWidget(self.table)

        splitter.addWidget(left_panel)

        #### lado direito gráficos
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(6)

        lbl_graf = QLabel("Gráficos")
        lbl_graf.setObjectName("titulo")
        right_layout.addWidget(lbl_graf)

        self.figure = Figure(facecolor=DARK)
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)

        splitter.addWidget(right_panel)
        splitter.setSizes([500, 900])
        root.addWidget(splitter)

    ### carregar os arquivos
    def carregar_arquivo(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Abrir arquivo", "", "Arquivos (*.csv *.xlsx)"
        )
        if not caminho:
            return

        df = pd.read_csv(caminho) if caminho.endswith(".csv") else pd.read_excel(caminho)

        colunas_necessarias = {"x1", "x2", "p"}
        if colunas_necessarias.issubset(df.columns):
            df["y"] = modelo(df["p"], df["x1"], df["x2"])
            self.df = df
            self.mostrar_tabela(df)
            self.mostrar_estatisticas(df)
            self.mostrar_anova(df)
            self.plotar_graficos(df)
            self.label.setText("✅ Arquivo carregado com sucesso")
        else:
            faltando = colunas_necessarias - set(df.columns)
            self.label.setText(f"❌ Erro: coluna(s) ausente(s): {', '.join(faltando)}")

    #### tabela dos dados 
    def mostrar_tabela(self, df):
        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])
        self.table.setHorizontalHeaderLabels(df.columns.tolist())
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                v = df.iat[i, j]
                texto = f"{v:.4f}" if isinstance(v, float) else str(v)
                item = QTableWidgetItem(texto)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j, item)
        self.table.resizeColumnsToContents()

    ## Estatística descritiva
    def mostrar_estatisticas(self, df):
        cols = ["x1", "x2", "y"]
        metricas = ["Mínimo", "Máximo", "Média", "Desvio Padrão", "Variância", "IC 95% (±)"]

        self.stat_table.setRowCount(len(metricas))
        self.stat_table.setColumnCount(len(cols))
        self.stat_table.setHorizontalHeaderLabels(cols)
        self.stat_table.setVerticalHeaderLabels(metricas)

        for j, col in enumerate(cols):
            s   = df[col].dropna()
            n   = len(s)
            std = s.std()
            ic  = stats.t.ppf(0.975, df=n - 1) * std / np.sqrt(n) if n > 1 else float("nan")
            for i, v in enumerate([s.min(), s.max(), s.mean(), std, s.var(), ic]):
                item = QTableWidgetItem(f"{v:.4f}")
                item.setTextAlignment(Qt.AlignCenter)
                self.stat_table.setItem(i, j, item)

        self.stat_table.resizeColumnsToContents()

    ##### ANOVA
    def mostrar_anova(self, df):
        grupos = [df[c].dropna().values for c in ["x1", "x2", "p", "y"]]
        f_stat, p_val = stats.f_oneway(*grupos)

        k          = len(grupos)
        n_total    = sum(len(g) for g in grupos)
        grand_mean = np.concatenate(grupos).mean()
        ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in grupos)
        ss_within  = sum(((g - g.mean()) ** 2).sum() for g in grupos)
        ss_total   = ss_between + ss_within
        df_between = k - 1
        df_within  = n_total - k
        ms_between = ss_between / df_between
        ms_within  = ss_within  / df_within

        headers = ["Fonte", "GL", "SQ", "QM", "F", "p-valor"]
        linhas  = [
            ["Entre grupos",      str(df_between), f"{ss_between:.4f}", f"{ms_between:.4f}", f"{f_stat:.4f}", f"{p_val:.4f}"],
            ["Dentro dos grupos", str(df_within),  f"{ss_within:.4f}",  f"{ms_within:.4f}",  "—",            "—"],
            ["Total",             str(n_total - 1), f"{ss_total:.4f}",  "—",                 "—",            "—"],
        ]

        self.anova_table.setRowCount(len(linhas))
        self.anova_table.setColumnCount(len(headers))
        self.anova_table.setHorizontalHeaderLabels(headers)

        from PyQt5.QtGui import QColor
        for i, row in enumerate(linhas):
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if j == 5 and i == 0:
                    try:
                        item.setForeground(QColor("#ef5350") if float(val) < 0.05 else QColor("#81c784"))
                    except ValueError:
                        pass
                self.anova_table.setItem(i, j, item)

        self.anova_table.resizeColumnsToContents()

    ######## Gráficos
    def plotar_graficos(self, df):
        self.figure.clear()
        self.figure.patch.set_facecolor(DARK)

        gs = self.figure.add_gridspec(2, 3, hspace=0.45, wspace=0.35,
                                      left=0.06, right=0.98,
                                      top=0.93, bottom=0.08)

        def scatter_tend(ax, x, y, cx, cy, xlabel, ylabel, legend_label, title):
            ax.scatter(x, y, color=cx, alpha=0.7,
                       edgecolors="white", linewidths=0.3, s=40, label=legend_label)
            m, b = np.polyfit(x, y, 1)
            xr = np.linspace(x.min(), x.max(), 200)
            ax.plot(xr, m * xr + b, color=cy, linewidth=1.5, linestyle="--", label="Tendência")
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.legend(fontsize=7, facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT)
            style_ax(ax, title)

        ax1 = self.figure.add_subplot(gs[0, 0])
        scatter_tend(ax1, df["x1"], df["y"], BLUE,   ORANGE, "DAP (cm)",    "Biomassa (kg)", "y × DAP", "Dispersão: y × DAP")

        ax2 = self.figure.add_subplot(gs[0, 1])
        scatter_tend(ax2, df["x2"], df["y"], GREEN,  RED,    "Altura (m)", "Biomassa (kg)", "y × H",   "Dispersão: y × H")

        ax3 = self.figure.add_subplot(gs[0, 2])
        scatter_tend(ax3, df["p"],  df["y"], ORANGE, BLUE,   "Densidade básica", "Biomassa (kg)", "y × ρ", "Dispersão: y × ρ")

        # Scatter y por índice
        ax4 = self.figure.add_subplot(gs[1, 0])
        ax4.scatter(range(len(df)), df["y"], color=ORANGE, alpha=0.75,
                    edgecolors="white", linewidths=0.3, s=35)
        ax4.plot(df["y"].values, color=BLUE, linewidth=1, alpha=0.5)
        ax4.set_xlabel("Índice")
        ax4.set_ylabel("Biomassa (kg)")
        style_ax(ax4, "Dispersão: y (série)")

        # Boxplot p variáveis de entrada
        ax5 = self.figure.add_subplot(gs[1, 1])
        bp5 = ax5.boxplot(
            [df["x1"].dropna(), df["x2"].dropna()],
            labels=["DAP (x1)", "H (x2)"],
            patch_artist=True,
            medianprops=dict(color=ORANGE, linewidth=2),
            whiskerprops=dict(color=TEXT),
            capprops=dict(color=TEXT),
            flierprops=dict(markerfacecolor=RED, marker="o", markersize=4, alpha=0.6),
            boxprops=dict(linewidth=1.2),
        )
        for patch, cor in zip(bp5["boxes"], [BLUE, GREEN, ORANGE]):
            patch.set_facecolor(cor)
            patch.set_alpha(0.6)
        style_ax(ax5, "Boxplot: variáveis de entrada")

        # Boxplot ###$##
        ax6 = self.figure.add_subplot(gs[1, 2])
        bp6 = ax6.boxplot(
            [df["y"].dropna()],
            labels=["Biomassa (y)"],
            patch_artist=True,
            medianprops=dict(color=ORANGE, linewidth=2),
            whiskerprops=dict(color=TEXT),
            capprops=dict(color=TEXT),
            flierprops=dict(markerfacecolor=RED, marker="o", markersize=4, alpha=0.6),
            boxprops=dict(linewidth=1.2),
        )
        bp6["boxes"][0].set_facecolor(BLUE)
        bp6["boxes"][0].set_alpha(0.6)
        style_ax(ax6, "Boxplot: biomassa estimada (y)")

        self.canvas.draw()

    #### Exportar
    def exportar_resultado(self):
        if self.df is None:
            self.label.setText("❌ Nenhum dado carregado para exportar.")
            return

        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar resultado", "", "Excel (*.xlsx);;CSV (*.csv)"
        )
        if not caminho:
            return

        df = self.df.copy()
        cols_stat = ["x1", "x2", "p", "y"]
        metricas  = ["Mínimo", "Máximo", "Média", "Desvio Padrão", "Variância", "IC 95% (±)"]

        ## tab estatísticas
        stat_rows = []
        for col in cols_stat:
            s   = df[col].dropna()
            n   = len(s)
            std = s.std()
            ic  = stats.t.ppf(0.975, df=n - 1) * std / np.sqrt(n) if n > 1 else float("nan")
            stat_rows.append([col, s.min(), s.max(), s.mean(), std, s.var(), ic])
        df_stat = pd.DataFrame(stat_rows, columns=["Variável"] + metricas)

        ##### ANOVA
        grupos     = [df[c].dropna().values for c in cols_stat]
        f_stat, p_val = stats.f_oneway(*grupos)
        k          = len(grupos)
        n_total    = sum(len(g) for g in grupos)
        grand_mean = np.concatenate(grupos).mean()
        ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in grupos)
        ss_within  = sum(((g - g.mean()) ** 2).sum() for g in grupos)
        ss_total   = ss_between + ss_within
        df_between = k - 1
        df_within  = n_total - k
        ms_between = ss_between / df_between
        ms_within  = ss_within  / df_within
        df_anova = pd.DataFrame([
            ["Entre grupos",      df_between, ss_between, ms_between, f_stat, p_val],
            ["Dentro dos grupos", df_within,  ss_within,  ms_within,  None,   None],
            ["Total",             n_total - 1, ss_total,  None,       None,   None],
        ], columns=["Fonte", "GL", "SQ", "QM", "F", "p-valor"])

        #salva as tabelas
        if caminho.endswith(".csv"):
            with open(caminho, "w", encoding="utf-8-sig") as f:
                f.write("=== DADOS ===\n")
                df.to_csv(f, index=False)
                f.write("\n=== ESTATÍSTICAS DESCRITIVAS ===\n")
                df_stat.to_csv(f, index=False)
                f.write("\n=== ANOVA ===\n")
                df_anova.to_csv(f, index=False)
        else:
            if not caminho.endswith(".xlsx"):
                caminho += ".xlsx"
            with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
                df.to_excel(writer,       sheet_name="Dados",        index=False)
                df_stat.to_excel(writer,  sheet_name="Estatísticas",  index=False)
                df_anova.to_excel(writer, sheet_name="ANOVA",         index=False)

        #salva os gráficos
        base     = caminho.rsplit(".", 1)[0]
        fig_path = base + "_graficos.png"
        self.figure.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=DARK)

        self.label.setText(f"✅ Exportado: {caminho}  |  gráficos: {fig_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = App()
    janela.show()
    sys.exit(app.exec_())