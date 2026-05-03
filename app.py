import sys
import numpy as np
import pandas as pd
from scipy import stats
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QSplitter, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from model import modelo

################### Parte visual do app 
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
    color: #81c784;
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
    color: #a8c7fa;
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

#################### Parte dos elementos do app
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Biomassa - Hymenolobium petraeum") # titulo para o topo da janela
        self.setGeometry(100, 80, 1400, 820)
        self.df = None
        self._build_ui()
        self.setStyleSheet(STYLE)

    #################################
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Barra superior ########################################## top = QHBoxLayout()
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

        lbl_stat = QLabel("Equação: y = 0,0673 * (0,56 * DAP^2 * H)^0,976")
        lbl_stat.setObjectName("titulo")
        left_layout.addWidget(lbl_stat)

        lbl_stat = QLabel("📊 Estatísticas Descritivas")
        lbl_stat.setObjectName("titulo")
        left_layout.addWidget(lbl_stat)

        self.stat_table = QTableWidget()
        self.stat_table.setMinimumHeight(200)
        left_layout.addWidget(self.stat_table)

        lbl_anova = QLabel("🔬 ANOVA (x1, x2, y)")
        lbl_anova.setObjectName("titulo")
        left_layout.addWidget(lbl_anova)

        self.anova_table = QTableWidget()
        self.anova_table.setMinimumHeight(100)
        left_layout.addWidget(self.anova_table)

        lbl_dados = QLabel("📋 Dados Carregados")
        lbl_dados.setObjectName("titulo")
        left_layout.addWidget(lbl_dados)

        self.table = QTableWidget()
        left_layout.addWidget(self.table)

        splitter.addWidget(left_panel)

        # Painel direito #########
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(6)

        lbl_graf = QLabel("📈 Gráficos")
        lbl_graf.setObjectName("titulo")
        right_layout.addWidget(lbl_graf)

        self.figure = Figure(facecolor="#1a1f2e")
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)

        splitter.addWidget(right_panel)
        splitter.setSizes([480, 880])

        root.addWidget(splitter)

    # ##########################################
    # Carregamento####
    def carregar_arquivo(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Abrir arquivo", "", "Arquivos (*.csv *.xlsx)"
        )
        if not caminho:
            return

        df = pd.read_csv(caminho) if caminho.endswith(".csv") else pd.read_excel(caminho)

        if "x1" in df.columns and "x2" in df.columns:
            df["y"] = modelo(df["x1"], df["x2"])
            self.df = df
            self.mostrar_tabela(df)
            self.mostrar_estatisticas(df)
            self.mostrar_anova(df)
            self.plotar_graficos(df)
            self.label.setText("✅ Arquivo carregado com sucesso")
        else:
            self.label.setText("❌ Erro: o arquivo precisa ter colunas x1 (Dap) e x2 (H)")

    #######################################/
    #Tabela de dados ############
    def mostrar_tabela(self, df):
        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])
        self.table.setHorizontalHeaderLabels(df.columns.tolist())
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                item = QTableWidgetItem(f"{df.iat[i, j]:.4f}"
                                        if isinstance(df.iat[i, j], float)
                                        else str(df.iat[i, j]))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j, item)
        self.table.resizeColumnsToContents()

    ###########################################
    #Estatísticas descritivas

    def mostrar_estatisticas(self, df):
        cols = ["x1", "x2", "y"]
        metricas = ["Mínimo", "Máximo", "Média", "Desvio Padrão",
                    "Variância", "IC 95% (±)"]

        self.stat_table.setRowCount(len(metricas))
        self.stat_table.setColumnCount(len(cols))
        self.stat_table.setHorizontalHeaderLabels(cols)
        self.stat_table.setVerticalHeaderLabels(metricas)

        for j, col in enumerate(cols):
            s = df[col].dropna()
            n = len(s)
            mean = s.mean()
            std = s.std()
            ic = stats.t.ppf(0.975, df=n - 1) * std / np.sqrt(n) if n > 1 else float("nan")
            valores = [s.min(), s.max(), mean, std, s.var(), ic]
            for i, v in enumerate(valores):
                item = QTableWidgetItem(f"{v:.4f}")
                item.setTextAlignment(Qt.AlignCenter)
                self.stat_table.setItem(i, j, item)

        self.stat_table.resizeColumnsToContents()

    ###########################################
    #ANOVA one-way (x1, x2, y)
    def mostrar_anova(self, df):
        grupos = [df["x1"].dropna().values,
                  df["x2"].dropna().values,
                  df["y"].dropna().values]

        f_stat, p_val = stats.f_oneway(*grupos)

        #Cálculo manual para tabela completa
        k = len(grupos)
        n_total = sum(len(g) for g in grupos)
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
            ["Entre grupos",
             f"{ss_between:.4f}", str(df_between),
             f"{ms_between:.4f}", f"{f_stat:.4f}", f"{p_val:.4f}"],
            ["Dentro dos grupos",
             f"{ss_within:.4f}", str(df_within),
             f"{ms_within:.4f}", "—", "—"],
            ["Total",
             f"{ss_total:.4f}", str(n_total - 1),
             "—", "—", "—"],
        ]

        self.anova_table.setRowCount(len(linhas))
        self.anova_table.setColumnCount(len(headers))
        self.anova_table.setHorizontalHeaderLabels(headers)

        for i, row in enumerate(linhas):
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                #destaca o p-valor 
                if j == 5 and i == 0:
                    try:
                        if float(val) < 0.05:
                            item.setForeground(
                                __import__("PyQt5.QtGui", fromlist=["QColor"]).QColor("#ef5350"))
                        else:
                            item.setForeground(
                                __import__("PyQt5.QtGui", fromlist=["QColor"]).QColor("#81c784"))
                    except ValueError:
                        pass
                self.anova_table.setItem(i, j, item)

        self.anova_table.resizeColumnsToContents()

    ###########################################
    # Gráficos ########
    def plotar_graficos(self, df):
        self.figure.clear()

        DARK   = "#1a1f2e"
        PANEL  = "#232a3b"
        GRID   = "#2e3a50"
        TEXT   = "#cdd8f0"
        GREEN  = "#4caf50"
        BLUE   = "#42a5f5"
        ORANGE = "#ffa726"
        RED    = "#ef5350"

        self.figure.patch.set_facecolor(DARK)

        def style_ax(ax, title):
            ax.set_facecolor(PANEL)
            ax.tick_params(colors=TEXT, labelsize=9)
            ax.set_title(title, color=TEXT, fontsize=10, fontweight="bold", pad=8)
            for spine in ax.spines.values():
                spine.set_edgecolor(GRID)
            ax.xaxis.label.set_color(TEXT)
            ax.yaxis.label.set_color(TEXT)
            ax.grid(True, color=GRID, linewidth=0.5, linestyle="--", alpha=0.6)

        #Layout: 2 linhas × 2 colunas
        #  [0,0] scatter y vs x1   [0,1] scatter y vs x2
        #  [1,0] scatter y (série) [1,1] boxplot
        gs = self.figure.add_gridspec(2, 2, hspace=0.42, wspace=0.35,
                                      left=0.07, right=0.97,
                                      top=0.93, bottom=0.08)

        #Scatter y vs x1
        ax1 = self.figure.add_subplot(gs[0, 0])
        ax1.scatter(df["x1"], df["y"], color=BLUE, alpha=0.7,
                    edgecolors="white", linewidths=0.3, s=40, label="Biomassa vs Dap")
        #linha de tendência
        m, b = np.polyfit(df["x1"], df["y"], 1)
        xr = np.linspace(df["x1"].min(), df["x1"].max(), 200)
        ax1.plot(xr, m * xr + b, color=ORANGE, linewidth=1.5, linestyle="--", label="Tendência")
        ax1.set_xlabel("x1")
        ax1.set_ylabel("y")
        ax1.legend(fontsize=8, facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT)
        style_ax(ax1, "Dispersão: y × x1")

        #Scatter y vs x2
        ax2 = self.figure.add_subplot(gs[0, 1])
        ax2.scatter(df["x2"], df["y"], color=GREEN, alpha=0.7,
                    edgecolors="white", linewidths=0.3, s=40, label="Biomassa vs H")
        m2, b2 = np.polyfit(df["x2"], df["y"], 1)
        xr2 = np.linspace(df["x2"].min(), df["x2"].max(), 200)
        ax2.plot(xr2, m2 * xr2 + b2, color=RED, linewidth=1.5, linestyle="--", label="Tendência")
        ax2.set_xlabel("x2")
        ax2.set_ylabel("y")
        ax2.legend(fontsize=8, facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT)
        style_ax(ax2, "Dispersão: y × x2")

        #Scatter y por índice 
        ax3 = self.figure.add_subplot(gs[1, 0])
        ax3.scatter(range(len(df)), df["y"], color=ORANGE, alpha=0.75,
                    edgecolors="white", linewidths=0.3, s=35)
        ax3.plot(df["y"].values, color=BLUE, linewidth=1, alpha=0.5)
        ax3.set_xlabel("Índice")
        ax3.set_ylabel("y")
        style_ax(ax3, "Dispersão: y (série temporal)")

        #Boxplot ##########################################        ax4 = self.figure.add_subplot(gs[1, 1])
        bplot = ax4.boxplot(
            [df["y"].dropna(), df["x1"].dropna(), df["x2"].dropna()],
            labels=["y", "x1", "x2"],
            patch_artist=True,
            medianprops=dict(color=ORANGE, linewidth=2),
            whiskerprops=dict(color=TEXT),
            capprops=dict(color=TEXT),
            flierprops=dict(markerfacecolor=RED, marker="o", markersize=4, alpha=0.6),
            boxprops=dict(linewidth=1.2),
        )
        colors = [BLUE, GREEN, ORANGE]
        for patch, color in zip(bplot["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        style_ax(ax4, "Boxplot: y, x1, x2")

        self.canvas.draw()

    #########################################
    #Exportar
    def exportar_resultado(self):
        if self.df is not None:
            caminho, _ = QFileDialog.getSaveFileName(
                self, "Salvar arquivo", "", "CSV (*.csv)"
            )
            if caminho:
                self.df.to_csv(caminho, index=False)
                self.label.setText("✅ Arquivo exportado com sucesso")


# ##########################################
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = App()
    janela.show()
    sys.exit(app.exec_())