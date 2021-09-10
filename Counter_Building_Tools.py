# Web Application for Coutning tools
# Creator: Marc Olivier Bertoz
# Education: Management Engineering; Data Science
# Date of Creation: 08.09.2021

# Loading package
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date

st.set_page_config(layout="wide")

# for spreadsheet information
from gspread_pandas import Spread,Client
from google.oauth2 import service_account


# Disable certificate verification 
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Create Google Authentication connection object ##################################3
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes = scope)
client = Client(scope=scope,creds=credentials)
spreadsheetname = "Test_streamlit"
spread = Spread(spreadsheetname,client = client)

# Check the connection ##################################################
# st.write(spread.url)

sh = client.open(spreadsheetname)
worksheet_list = sh.worksheets()


# Functions ###############################################################

# Get worksheet names
def worksheet_names():
    sheet_names = []
    for sheet in worksheet_list:
        sheet_names.append(sheet.title)
    return sheet_names

# Get the sheet as dataframe
def load_the_spreadsheet(spreadsheetname):
    worksheet = sh.worksheet(spreadsheetname)
    df = pd.DataFrame(worksheet.get_all_records())
    return df    

# Update to Sheet
def update_the_spreadsheet(spreadsheetname,dataframe):
    col = ['Oggetto','Quantità_Entrata','Quantità_Uscita','Totale_Stock','Data'] 
    spread.df_to_sheet(dataframe[col],sheet = spreadsheetname,index = False)   
    st.sidebar.info('Updated to GoogleSheet')


# Loading data
def load_data():
    # Checking if google sheets exist
    # what_sheets = worksheet_names()
    data = load_the_spreadsheet('Foglio1')
    return data

# Compute the new stock
def compute_new_stock(df,object,qta_entry,qta_exit):
    # Get old stock
    df_object = df[df['Oggetto'] == object].iloc[-1:]
    value_actual_stock = int(df_object['Totale_Stock'])
    # Compute new stock
    if value_actual_stock != 0:
        new_stock = value_actual_stock - qta_exit +qta_entry
        return new_stock
    elif value_actual_stock == 0:
        st.warning('Aggiungere stock iniziale')


################################################################################

# Get today date
now = date.today().strftime("%d/%m/%Y")

# Retrive the dataframe
df = load_data()

# Creating columns
left_column1, right_column1 = st.columns(2)

# Displaying the dataframe
left_column1.header('Foglio Google Sheets')
left_column1.dataframe(df)

# First plot, on the right column 1, all stock throught time of all objects
right_column1.header('Andamento nel tempo dello stock di tutti gli oggetti')
all_stocks = px.line(df, x='Data', y=['Totale_Stock'], color='Oggetto')
right_column1.plotly_chart(all_stocks)

# Sidebar option #######################################################################################

sidebar = st.sidebar
sidebar.title('Operazioni')
operazioni = sidebar.radio('Selezionare Operazione',('Aggiungere Nuovo Stock','Modificare Stock','Controllo Ulteriori Grafici'))

if operazioni == 'Aggiungere Nuovo Stock':
    sidebar.header('Informazioni')
    sidebar.write('Qui di seguito si può aggiungere nuovo stock NON presente di un determinato oggetto')
    # Aggiungere Stock #########
    Object_Add = sidebar.text_input('Oggetto')
    Qta_Stock_Add = sidebar.number_input('Quantità', min_value= 0, max_value= 100000,step=1)

    # Create button for adding new stock
    button_add = sidebar.button('Aggiungi', key=1)
    if button_add:
        opt = {
            'Oggetto': [Object_Add],
            'Quantità_Entrata': [0],
            'Quantità_Uscita': [0],
            'Totale_Stock': [Qta_Stock_Add],
            'Data': [now]
        }
        opt_df = pd.DataFrame(opt)
        df1 = load_data()
        new_df = df1.append(opt_df, ignore_index=True)
        update_the_spreadsheet('Foglio1', new_df)
    ############################
elif operazioni == 'Modificare Stock':
    sidebar.header('Informazioni')
    sidebar.write('Qui di seguito è possibile modificare lo stock presente di un determinato oggetto')
    # Loading the df
    df2 = load_data()

    # Modificare Stock #################
    Object_Edit = sidebar.selectbox('Selezionare Oggetto', sorted(df['Oggetto'].unique()))

    # state_select = st.sidebar.selectbox('Select a State', sorted(mass_shooting_df['State'].unique()))

    Qta_Entrata = sidebar.number_input('Quantità Entrata', min_value= 0, max_value= 100000,step=1)
    Qta_Uscita = sidebar.number_input('Quantità Uscita', min_value= 0, max_value= 100000,step=1)

    button_edit = sidebar.button('Modifica', key=2)
    if button_edit:
        
        # Get last stock and compute new one
        Qta_Stock_Add = compute_new_stock(df2,Object_Edit,Qta_Entrata,Qta_Uscita)


        opt = {
            'Oggetto': [Object_Edit],
            'Quantità_Entrata': [Qta_Entrata],
            'Quantità_Uscita': [Qta_Uscita],
            'Totale_Stock': [Qta_Stock_Add],
            'Data': [now]
        }
        opt_df = pd.DataFrame(opt)
        new_df = df2.append(opt_df, ignore_index=True)
        update_the_spreadsheet('Foglio1', new_df)
    # Qta_Stock_Add = sidebar.number_input('Quantità', min_value= 1, max_value= 100000,step=1)
    ###################################3
elif operazioni == 'Controllo Ulteriori Grafici': 
    sidebar.header('Informazioni')
    sidebar.write('Qui di seguito è possibile visualizzare i grafici per il singolo oggetto')
    # Load data
    df3 = load_data()
    
    # Second plot, stock and operaiton throught time of single object
    left_column2, right_column2 = st.columns(2)
    
    Object_Plot = sidebar.selectbox('Selezionare Oggetto', sorted(df3['Oggetto'].unique()))

    left_column2.header('Andamento Stock oggetto: ' + Object_Plot)
    
    right_column2.header('Andamento Operazioni oggetto: ' + Object_Plot)

    button_view = sidebar.button('Visualizza', key=3)
    if button_view:
        object_data = df3[df3['Oggetto'] == Object_Plot]
        # Left plot
        plot_single_object = px.line(object_data, x='Data', y='Totale_Stock')
        left_column2.plotly_chart(plot_single_object)
        # Right plot
        plot_object_operations = px.line(object_data, x='Data', y=['Quantità_Entrata','Quantità_Uscita'])
        right_column2.plotly_chart(plot_object_operations)
        


# Web Application for Coutning tools
# Creator: Marc Olivier Bertoz
# Education: Management Engineering; Data Science
# Date of Creation: 08.09.2021





























