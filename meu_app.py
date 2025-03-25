import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime
import warnings
import time

warnings.simplefilter(action='ignore', category=FutureWarning)

st.set_page_config(page_title="Go MED SAÚDE", page_icon=":bar_chart:", layout="wide")

# Configurações Globais
CAMINHO_ARQUIVO_VENDAS = "df_vendas.csv"
MESES_ABREVIADOS = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

def carregar_dados(caminho_arquivo):
    """Carrega os dados de vendas de um arquivo CSV."""
    try:
        df = pd.read_csv(caminho_arquivo)
        if df.empty:
            st.warning("O arquivo CSV está vazio.")
            return None
        return df
    except FileNotFoundError:
        st.error("Arquivo não encontrado!")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
        return None

def formatar_moeda(valor, simbolo_moeda="R$"):
    """Formata um valor numérico como moeda."""
    if pd.isna(valor):
        return ''
    try:
        return f"{simbolo_moeda} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "Valor inválido"

def calcular_metricas(df):
    """Calcula métricas de vendas."""
    total_nf = len(df['NF'].unique())
    total_qtd_produto = df['Qtd_Produto'].sum()
    valor_total_item = df['Valor_Total_Item'].sum()
    total_custo_compra = df['Total_Custo_Compra'].sum()
    total_lucro_venda = df['Total_Lucro_Venda_Item'].sum()
    return total_nf, total_qtd_produto, valor_total_item, total_custo_compra, total_lucro_venda

def agrupar_e_somar(df, coluna_agrupamento):
    """Agrupa e soma valores por uma coluna."""
    return df.groupby(coluna_agrupamento).agg(
        {'Valor_Total_Item': 'sum', 'Total_Custo_Compra': 'sum', 'Total_Lucro_Venda_Item': 'sum'}
    ).reset_index()

def ranking_clientes(df, top_n=10,max_len=25):
    """Retorna os top N clientes com maior faturamento total, incluindo o número do ranking."""
    df_clientes = df.groupby('Cliente').agg({'Valor_Total_Item': 'sum'}).reset_index()
    df_clientes = df_clientes.sort_values(by='Valor_Total_Item', ascending=False).head(top_n)
    df_clientes['Ranking'] = range(1, len(df_clientes) + 1)
    df_clientes['Valor_Total_Item'] = df_clientes['Valor_Total_Item'].apply(formatar_moeda)
    df_clientes = df_clientes[['Ranking', 'Cliente', 'Valor_Total_Item']]
    df_clientes['Cliente'] = df_clientes['Cliente'].str[:max_len]
    return df_clientes

def produtos_mais_vendidos(df, top_n=10, ordenar_por='Valor_Total_Item', max_len=30):
    df_agrupado = df.groupby('Descricao_produto')[ordenar_por].sum().reset_index()
    df_ordenado = df_agrupado.sort_values(by=ordenar_por, ascending=False)
    df_ordenado['Descricao_produto'] = df_ordenado['Descricao_produto'].str[:max_len]
    return df_ordenado.head(top_n)
def criar_grafico_barras(df, x, y, title, labels):
    df = df.sort_values(by=y, ascending=False) 
    df = df.iloc[::-1]
    df['Valor_Monetario'] = df['Valor_Total_Item'].apply(formatar_moeda)
    fig = px.bar(df, x=y, y=x,
                 title=title,
                 labels={labels.get(y, y): labels.get(x, x), labels.get(x, x): labels.get(y, y)},
                 color=y,
                 text=df['Valor_Monetario'],
                 template="ggplot2",
                 hover_data={y: False, x: False, 'Valor_Monetario': True},
                 orientation='h')
    fig.update_traces(
        marker=dict(line=dict(color='black', width=1)),
        hoverlabel=dict(bgcolor="black", font_size=22, font_family="Arial, sans-serif"),
        textfont=dict(size=28, color='white'),
        textangle=0,
        textposition='inside'
    )
    fig.update_layout(
        yaxis_title=labels.get(x, x),
        xaxis_title=labels.get(y, y),
        showlegend=False,
        height=850,
        width=400,
        xaxis=dict(tickfont=dict(size=18)),
        yaxis=dict(
            title=dict(
                text=labels.get(x, x),
                font=dict(size=18)
            ),
            tickfont=dict(size=16),
        ),
        title_font=dict(size=40, family="Times New Roman"),
        margin=dict(l=10, r=10)
    )
    return fig


def criar_grafico_vendas_diarias(df, mes, ano):
    df_filtrado = df[(df['Mes'] == mes) & (df['Ano'] == ano)]
    vendas_diarias = df_filtrado.groupby('Dia')['Valor_Total_Item'].sum().reset_index()
    vendas_diarias["Valor_Monetario"] = vendas_diarias["Valor_Total_Item"].apply(formatar_moeda)
    fig = px.bar(
        vendas_diarias, x='Dia', y='Valor_Total_Item',
        title=f'Vendas Diárias em {mes}/{ano}',
        labels={'Dia': 'Dia', 'Valor_Total_Item': 'Valor Total de Venda'},
        color='Valor_Total_Item',
        text=vendas_diarias["Valor_Monetario"],
        template="plotly_white", hover_data={'Valor_Total_Item': False,'Valor_Monetario': True})
    fig.update_traces(
        marker=dict(line=dict(color='black', width=1)),
        hoverlabel=dict(bgcolor="black", font_size=22,
            font_family="Arial-bold, sans-serif"), 
            textfont=dict(size=16, color='black'),
            textangle=0, textposition='inside')
    fig.update_layout(yaxis_title='Valor Total de Venda',
        xaxis_title='Dia',
        showlegend=False, height=400, 
        xaxis=dict(tickfont=dict(size=18)),
        yaxis=dict(
            title=dict(
                text='Valor Total de Venda',
                font=dict(size=14)
            ),
            tickfont=dict(size=12)
        ),
        title_font=dict(size=40, family="Times New Roman")
    )
    return fig


def exibir_grafico_ticket_medio(df_ticket_medio):
    df_ticket_medio['Ticket Medio'] = df_ticket_medio['Ticket_Medio'].apply(formatar_moeda)
    fig = px.bar(
        df_ticket_medio,
        x="Vendedor",
        y="Ticket_Medio",
        color="Semana",
        barmode="group",
        title="Ticket Médio por Vendedor e Semana",
        labels={"Ticket_Medio": "Ticket Médio", "Vendedor": "Vendedor", "Semana": "Semana"},
        text=df_ticket_medio["Ticket Medio"],
        template="plotly_dark",
        hover_data={"Vendedor": False, "Ticket_Medio": False, 'Ticket Medio': True}
    )
    fig.update_traces(
        marker=dict(line=dict(color='black', width=1)),
        hoverlabel=dict(bgcolor="black", font_size=22, font_family="Arial, sans-serif"),
        textfont=dict(size=32, color='#000000'),
        textposition='outside',
        cliponaxis=False
    )
        
    fig.update_layout(
        yaxis_title="Ticket Médio",
        xaxis_title="Vendedor",
        showlegend=True,
        height=500,
        xaxis=dict(tickfont=dict(size=18)),
        yaxis=dict(
            title=dict(
                text="Ticket Médio",
                font=dict(size=18)
            ),
            tickfont=dict(size=16),
        ),
        title_font=dict(size=40, family="Times New Roman"),
        legend=dict(
            title="Semanas",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1,
            font=dict(
                size=14,  
                family="Arial, sans-serif",  
                color="white",
            )
        ),
        bargap=0.1
    )
    return fig

def aplicar_filtros(df, vendedor='Todos', mes=None, ano=None, situacao='Faturada'):
    """Aplica filtros aos dados."""
    df_filtrado = df.copy()
    if ano is None:
        ano = datetime.datetime.now().year
    if mes is None:
        mes = datetime.datetime.now().month
    if vendedor != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Vendedor'] == vendedor]
    if mes is not None:
        df_filtrado = df_filtrado[df_filtrado['Mes'] == mes]
    if ano is not None:
        df_filtrado = df_filtrado[df_filtrado['Ano'] == ano]
    if situacao != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['situacao'] == situacao]
    return df_filtrado

def processar_dados_ticket_medio(df):
    df['Data_Emissao'] = pd.to_datetime(df['Data_Emissao'], format='mixed', dayfirst=True)
    df['Semana'] = df['Data_Emissao'].dt.isocalendar().week
    colunas_nf_unicas = ['NF', 'Data_Emissao', 'Vendedor', 'Valor_Total_Nota', 'Mes', 'Ano', 'Semana', 'situacao']
    df_nf_unicas = df.drop_duplicates(subset='NF')[colunas_nf_unicas].copy()
    df_nf_unicas = df_nf_unicas[df_nf_unicas['situacao'] == 'Faturada']

    ano_atual = datetime.datetime.now().year
    mes_atual = datetime.datetime.now().month

    df_nf_unicas = aplicar_filtros(df_nf_unicas, mes=mes_atual, ano=ano_atual)

    df_resumo = df_nf_unicas.groupby(['Ano', 'Mes', 'Semana', 'Vendedor'])['NF'].count().reset_index(name='Quantidade_Notas_Semana')
    df_nf_unicas = pd.merge(df_nf_unicas, df_resumo, on=['Ano', 'Mes', 'Semana', 'Vendedor'], how='left')
    df_nf_unicas['Quantidade_Notas_Semana'] = df_nf_unicas['Quantidade_Notas_Semana'].fillna(0).astype(int)

    df_resumo_vendas = df_nf_unicas.groupby(['Ano', 'Mes', 'Semana', 'Vendedor'])['Valor_Total_Nota'].sum().reset_index(name='Soma_Venda_Semana')
    df_nf_unicas = pd.merge(df_nf_unicas, df_resumo_vendas, on=['Ano', 'Mes', 'Semana', 'Vendedor'], how='left')

    df_ticket_medio = df_nf_unicas.groupby(['Vendedor', 'Semana'])['Valor_Total_Nota'].mean().reset_index(name='Ticket_Medio')
    df_ticket_medio['Ticket Medio'] = df_ticket_medio['Ticket_Medio'].apply(formatar_moeda)
    
    return df_ticket_medio

def criar_grafico_pizza_vendas_linha(df):
    """Cria um gráfico de pizza mostrando as vendas por linha de produto."""
    df_linha = df.groupby('Linha')['Valor_Total_Item'].sum().reset_index()
    fig = px.pie(df_linha, values='Valor_Total_Item', names='Linha', 
                 title='Vendas por Linha de Produto', 
                 hover_data=['Valor_Total_Item'])
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        textfont=dict(size=22)  
    )
    fig.update_layout(
        height=700,
        showlegend=True,
        title_font=dict(size=40, family="Times New Roman")
    )
    return fig




def renderizar_pagina_vendas_parte1(df):
    df_filtrado = aplicar_filtros(df)

    ano_atual = datetime.datetime.now().year
    mes_atual = datetime.datetime.now().month

    total_nf, total_qtd_produto, valor_total_item, total_custo_compra, total_lucro_venda = calcular_metricas(df_filtrado)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total de Notas", f"{total_nf}")
    col2.metric("Total de Produtos", f"{total_qtd_produto}")
    col3.metric("Faturamento Total", formatar_moeda(valor_total_item))
    col4.metric("Custo Total", formatar_moeda(total_custo_compra))
    col5.metric("Margem Bruta", formatar_moeda(total_lucro_venda))

    if 'Dia' in df.columns:
            fig_vendas_diarias = criar_grafico_vendas_diarias(df_filtrado, mes_atual, ano_atual)
            st.plotly_chart(fig_vendas_diarias)


    col_graf1, col_graf2= st.columns([3,3])

        

    with col_graf1:

    
        fig_vendedor = criar_grafico_barras(agrupar_e_somar(df_filtrado, 'Vendedor'), 'Vendedor', 'Valor_Total_Item',
                                            'Vendas por Vendedor', {'Valor_Total_Item': 'Valor Total de Venda'})
        st.plotly_chart(fig_vendedor)



    with col_graf2:

        fig_produtos = criar_grafico_barras(produtos_mais_vendidos(df_filtrado), 'Descricao_produto', 'Valor_Total_Item',
                                            'Top 10 Produtos Mais Vendidos',
                                            {'Descricao_produto': 'Produto', 'Valor_Total_Item': 'Valor Total de Venda'})
        st.plotly_chart(fig_produtos)

def renderizar_pagina_vendas_parte2(df):
    df_filtrado = aplicar_filtros(df)

    df_ticket_medio = processar_dados_ticket_medio(df_filtrado)

    df_ranking = ranking_clientes(df_filtrado)
    df_ranking = df_ranking.reset_index(drop=True)
    df_ranking = df_ranking.iloc[::-1]

    fig = px.bar(
        df_ranking,
        x="Valor_Total_Item",
        y="Cliente",
        orientation="h",
        title="Top Clientes por Faturamento (Personalizado)",
        labels={"Valor_Total_Item": "Faturamento (R$)", "Cliente": "Clientes"},
        text=df_ranking["Valor_Total_Item"],
        color="Valor_Total_Item", 
        color_continuous_scale="Viridis"
    )

    fig.update_traces(
        textposition="inside",
        textfont=dict(size=28, color="black") 
    )

    fig.update_layout(
        xaxis_showticklabels=True,
        height=800,
        width=300,
        yaxis=dict(
            title=dict(font=dict(size=24)),
            tickfont=dict(size=16)
        ),
        xaxis=dict(
        tickfont=dict(size=16)
        ),
        title_font=dict(size=40, family="Times New Roman")
        
    )

    st.plotly_chart(exibir_grafico_ticket_medio(df_ticket_medio))

    col_graf4, col_graf5 = st.columns([2,3])

    with col_graf4:

        
        fig_pizza_linha = criar_grafico_pizza_vendas_linha(df_filtrado)
        st.plotly_chart(fig_pizza_linha)


    with col_graf5:
        st.plotly_chart(fig)        

        

def main():
    """Função principal para carregar dados e renderizar as páginas em loop."""
    caminho_arquivo = CAMINHO_ARQUIVO_VENDAS

    if caminho_arquivo and os.path.exists(caminho_arquivo):
        try:
            df = carregar_dados(caminho_arquivo)
            if df is not None:
                if 'pagina_atual' not in st.session_state:
                    st.session_state.pagina_atual = 1

                empty_space = st.empty()  

                if st.session_state.pagina_atual == 1:
                    with empty_space.container(): 
                        renderizar_pagina_vendas_parte1(df)
                    time.sleep(20)
                    st.session_state.pagina_atual = 2
                    st.rerun()

                elif st.session_state.pagina_atual == 2:
                    with empty_space.container(): 
                        renderizar_pagina_vendas_parte2(df)
                    time.sleep(20)
                    st.session_state.pagina_atual = 1
                    st.rerun()

        except Exception as e:
            st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
    else:
        st.error("Arquivo não encontrado!")

if __name__ == "__main__":
    main()