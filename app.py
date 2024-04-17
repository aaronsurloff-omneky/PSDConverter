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
                # Extracting bounding box coordinates
                bbox = layer.bbox
                print("Bounding box:", bbox)
                # Calculating location (x, y) of top right corner
                x = bbox[1][0]
                y = bbox[0][1]
                # Calculating height and width
                height = bbox[1][1] - bbox[0][1]
                width = bbox[1][0] - bbox[0][0]
                layer_info.append({
                    'name': layer.name,
                    'location': (x, y),
                    'height': height,
                    'width': width,
                    'kind': layer.kind,
                    'text': layer.text if layer.kind == 'type' else None
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
                # Extracting bounding box coordinates
                bbox = layer.bbox
                print("Bounding box:", bbox)
                # Calculating location (x, y) of top right corner
                x = bbox[1][0]
                y = bbox[0][1]
                # Calculating height and width
                height = bbox[1][1] - bbox[0][1]
                width = bbox[1][0] - bbox[0][0]
                group_info.append({
                    'name': f'{group.name}_part_{i}',
                    'location': (x, y),
                    'height': height,
                    'width': width,
                    'kind': layer.kind,
                    'text': layer.text if layer.kind == 'type' else None
                })

                img = layer.composite()
                img.save(os.path.join(output_dir, f'{group.name}_part_{i}.png'))

    return group_info

st.title("PSD Importer Prototype")
st.caption("This extracts visible layers, converts all non-images to PNG, outputs text, and tells us the location on the canvas for each exported part")

uploaded_file = st.file_uploader("Upload a PSD file", type=["psd"])

if uploaded_file is not None:
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
        st.write(f"Location: {layer['location']}")
        st.write(f"Height: {layer['height']} pixels")
        st.write(f"Width: {layer['width']} pixels")
        st.write(f"Kind: {layer['kind']}")
        if layer['kind'] == 'type':
            st.write(f"Text: {layer['text']}")
        st.write("")
