import io
import pandas as pd
import streamlit as st
import requests

import scrapers

st.set_page_config(page_title="Beauty Price Focused")

if 'results' not in st.session_state:
    st.session_state['results'] = pd.DataFrame()

st.title('Beauty Price Focused')

st.header('Carga de Archivo Maestro')
st.caption('Ejemplo de formato de archivo para búsqueda masiva:')
example_df = pd.DataFrame({
    'SKU': ['12345', '67890'],
    'Nombre': ['Producto Ejemplo 1', 'Producto Ejemplo 2']
})
st.table(example_df)
uploaded = st.file_uploader('Selecciona un CSV o Excel con nombres o SKUs', type=['csv','xlsx'])
if uploaded is not None:
    if uploaded.name.endswith('.csv'):
        df_input = pd.read_csv(uploaded)
    else:
        df_input = pd.read_excel(uploaded)
    st.write('Archivo cargado con', len(df_input), 'registros')
    if st.button('Iniciar scraping masivo'):
        session = requests.Session()
        resultados = []
        for _, row in df_input.iterrows():
            sku = row.get('SKU') or row.get('sku')
            nombre = row.get('nombre') or row.get('Nombre')
            if sku:
                res = scrapers.search_beautycreations_sku(str(sku), session=session)
                res.update({'criterio': sku, 'fuente': 'BeautyCreations'})
                resultados.append(res)
                res = scrapers.search_bellisima_sku(str(sku), session=session)
                res.update({'criterio': sku, 'fuente': 'Bellisima'})
                resultados.append(res)
            if nombre:
                res = scrapers.search_stefano_name(str(nombre), session=session)
                res.update({'criterio': nombre, 'fuente': 'Stefano'})
                resultados.append(res)
                res = scrapers.search_dubellay_name(str(nombre), session=session)
                res.update({'criterio': nombre, 'fuente': 'Dubellay'})
                resultados.append(res)
        df_res = pd.DataFrame(resultados)
        st.session_state['results'] = pd.concat([st.session_state['results'], df_res], ignore_index=True)
        st.success('Scraping completado')

st.header('Consulta Individual')
with st.form('single'):
    col1, col2 = st.columns(2)
    with col1:
        input_name = st.text_input('Nombre de Producto')
    with col2:
        input_sku = st.text_input('SKU')
    submitted = st.form_submit_button('Buscar')

if submitted:
    session = requests.Session()
    resultados = []
    if input_sku:
        res = scrapers.search_beautycreations_sku(input_sku, session=session)
        res.update({'criterio': input_sku, 'fuente': 'BeautyCreations'})
        resultados.append(res)
        res = scrapers.search_bellisima_sku(input_sku, session=session)
        res.update({'criterio': input_sku, 'fuente': 'Bellisima'})
        resultados.append(res)
    if input_name:
        res = scrapers.search_stefano_name(input_name, session=session)
        res.update({'criterio': input_name, 'fuente': 'Stefano'})
        resultados.append(res)
        res = scrapers.search_dubellay_name(input_name, session=session)
        res.update({'criterio': input_name, 'fuente': 'Dubellay'})
        resultados.append(res)
    df_res = pd.DataFrame(resultados)
    st.session_state['results'] = pd.concat([st.session_state['results'], df_res], ignore_index=True)
    st.success('Búsqueda completada')

st.header('Resultados Consolidados')
if not st.session_state['results'].empty:
    st.dataframe(st.session_state['results'])
    output = io.BytesIO()
    st.session_state['results'].to_excel(output, index=False)
    st.download_button('Descargar Excel', data=output.getvalue(), file_name='resultados.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
else:
    st.info('Sin resultados aún')
