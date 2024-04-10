import pandas as pd
import streamlit as st
import json

def load_settings():
    # load settings.json
    with open('settings.json') as f:
        settings = json.load(f)
    return settings

def save_settings(settings):
    # save settings.json
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

def main():

    settings = load_settings()

    st.header("Digitec Galaxus - Filialzielbestand")
    
    # settings
    with st.sidebar:
        with st.expander("Excel data"):
            file = st.text_input("File", settings["filepath"])
            n = st.number_input("Shift", min_value=1, value=2, step=1)
            try:
                df = pd.read_csv(file, skiprows=n)
            except:
                st.error("Please enter a valid file path.")

            columns = [col for col in df.columns.to_list() if not col.startswith("Unnamed")]
            product_id_name = st.selectbox("Product ID", columns, index=settings["product_id_name_index"])
            zielbestand_column = st.selectbox("Zielbestand", columns, index=settings["zielbestand_column_index"])
            bemerkungen_column = st.selectbox("Bemerkungen", columns, index=settings["bemerkungen_column_index"])
            bemerkungen_string_deutschweitz = st.text_input("Bemerkungen (Deutschweitz) str", value="Nur in Deutschschweiz")
            bemerkungen_string_franz = st.text_input("Bemerkungen (Franz) str (Startswith)", value="Franz nur in LA")

        with st.expander("Strategy"):
            max_transfers_per_run = st.number_input("Max transfers per run", min_value=1, value=settings["max_trans_default_value"], step=1)

        button = st.button("Save")
        if button:
            settings["filepath"] = file
            settings["product_id_name_index"] = columns.index(product_id_name)
            settings["zielbestand_column_index"] = columns.index(zielbestand_column)
            settings["bemerkungen_column_index"] = columns.index(bemerkungen_column)
            settings["bemerkungen_string_deutschweitz"] = bemerkungen_string_deutschweitz
            settings["bemerkungen_string_franz"] = bemerkungen_string_franz
            settings["max_trans_default_value"] = max_transfers_per_run
            save_settings(settings)

    with st.expander("Data"):
        st.write(df)

main()


# for every row in the dataframe
#for index, row in df.iterrows():
#    product = int(row["Product Id"])
#    zielbestand = int(row["Stück pro Filiale"])
#    bemerkungen = row['Bemerkungen']