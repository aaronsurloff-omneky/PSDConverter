import streamlit as st
import os
import tempfile
from psd_tools import PSDImage

def separate_parts(psd_file):
    psd = PSDImage.open(psd_file)
    output_dir = tempfile.mkdtemp()
    layer_info = []  # List to store layer information

    for i, layer in enumerate(psd):
        if layer.is_visible():
            if layer.is_group():
                group_info = extract_parts_from_group(layer, output_dir)
                layer_info.extend(group_info)
            else:
                if layer.kind == 'type':  # Check if layer is a text layer
                    text_data = extract_text_data(layer)
                else:
                    text_data = None

                layer_info.append({
                    'name': layer.name,
                    'bbox': layer.bbox,
                    'kind': layer.kind,
                    'text': text_data
                })

                img = layer.composite()
                img.save(os.path.join(output_dir, f'{layer.name}.png'))

    return output_dir, layer_info

def extract_parts_from_group(group, output_dir):
    group_info = []
    for i, layer in enumerate(group):
        if layer.is_visible():
            if layer.is_group():
                subgroup_info = extract_parts_from_group(layer, output_dir)
                group_info.extend(subgroup_info)
            else:
                if layer.kind == 'type':  # Check if layer is a text layer
                    text_data = extract_text_data(layer)
                else:
                    text_data = None

                group_info.append({
                    'name': f'{group.name}_part_{i}',
                    'bbox': layer.bbox,
                    'kind': layer.kind,
                    'text': text_data
                })

                img = layer.composite()
                img.save(os.path.join(output_dir, f'{group.name}_part_{i}.png'))

    return group_info

def extract_text_data(layer):
    # Extracting text content and other attributes
    text_data = {
        'content': layer.text,
        'font': getattr(layer, 'font', 'Default Font'),
        'color': layer.color,
        'color_hex': rgb_to_hex(layer.color)  # Convert RGB color to hex code
        # Add more text attributes as needed
    }
    return text_data

def rgb_to_hex(rgb_color):
    # Convert RGB color to hex code
    return '#{:02x}{:02x}{:02x}'.format(int(rgb_color.red), int(rgb_color.green), int(rgb_color.blue))

st.title("PSD Parts Separator")

uploaded_file = st.file_uploader("Upload a PSD file", type=["psd"])

if uploaded_file is not None:
    try:
        output_dir, layer_info = separate_parts(uploaded_file)
        st.write("Separation completed! Download the separated parts:")
        for filename in os.listdir(output_dir):
            st.download_button(
                label=filename,
                data=open(os.path.join(output_dir, filename), "rb").read(),
                file_name=filename,
                mime="image/png"
            )

        st.write("Layer Information:")
        for layer in layer_info:
            st.write(f"Name: {layer['name']}")
            st.write(f"Bounding Box: {layer['bbox']}")
            st.write(f"Kind: {layer['kind']}")
            if layer['kind'] == 'type':
                st.write("Text:")
                st.write(layer['text']['content'])
                st.write(f"Font: {layer['text']['font']}")
                st.write(f"Color: {layer['text']['color']}")
                st.write(f"Color (Hex): {layer['text']['color_hex']}")  # Display color as hex code
            st.write("")
    except Exception as e:
        st.error(f"An error occurred: {e}")