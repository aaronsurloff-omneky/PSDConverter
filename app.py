import streamlit as st
import os
import tempfile
from psd_tools import PSDImage

def separate_parts(psd_file):
    # Open the PSD file
    psd = PSDImage.open(psd_file)
    # Create a temporary directory to store output
    output_dir = tempfile.mkdtemp()
    # List to store layer information
    layer_info = []

    # Iterate through each layer in the PSD
    for i, layer in enumerate(psd):
        # Check if the layer is visible
        if layer.is_visible():
            # If layer is a group, extract parts from the group
            if layer.is_group():
                group_info = extract_parts_from_group(layer, output_dir)
                layer_info.extend(group_info)
            else:
                # If layer is a shape, save it as SVG
                if layer.kind == 'shape':
                    layer_info.append({
                        'name': layer.name,
                        'kind': layer.kind,
                        'svg_path': os.path.join(output_dir, f'{layer.name}.svg')
                    })
                    layer.save_as_svg(layer_info[-1]['svg_path'])  # Save layer as SVG
                else:
                    # If layer is not a shape, add it to layer_info
                    layer_info.append({
                        'name': layer.name,
                        'kind': layer.kind,
                        'text': layer.text if layer.kind == 'type' else None
                    })

    return output_dir, layer_info

def extract_parts_from_group(group, output_dir):
    group_info = []
    # Iterate through each layer in the group
    for i, layer in enumerate(group):
        # Check if the layer is visible
        if layer.is_visible():
            # If layer is a subgroup, extract parts from the subgroup
            if layer.is_group():
                subgroup_info = extract_parts_from_group(layer, output_dir)
                group_info.extend(subgroup_info)
            else:
                # If layer is a shape, save it as SVG
                if layer.kind == 'shape':
                    group_info.append({
                        'name': f'{group.name}_part_{i}',
                        'kind': layer.kind,
                        'svg_path': os.path.join(output_dir, f'{group.name}_part_{i}.svg')
                    })
                    layer.save_as_svg(group_info[-1]['svg_path'])  # Save layer as SVG
                else:
                    # If layer is not a shape, add it to group_info
                    group_info.append({
                        'name': f'{group.name}_part_{i}',
                        'kind': layer.kind,
                        'text': layer.text if layer.kind == 'type' else None
                    })

    return group_info

st.title("PSD Importer Prototype")
st.caption("This extracts visible layers, converts all shapes to SVG, outputs text, and tells us the location on the canvas for each exported part")

uploaded_file = st.file_uploader("Upload a PSD file", type=["psd"])

if uploaded_file is not None:
    # Separate the parts of the PSD file
    output_dir, layer_info = separate_parts(uploaded_file)
    # Display download buttons for SVG files
    st.write("Separation completed! Download the separated parts:")
    for layer in layer_info:
        if layer['kind'] == 'shape':
            st.download_button(
                label=layer['name'],
                data=open(layer['svg_path'], "rb").read(),
                file_name=f"{layer['name']}.svg",
                mime="image/svg+xml"
            )

    # Display layer information
    st.write("Layer Information:")
    for layer in layer_info:
        st.write(f"Name: {layer['name']}")
        st.write(f"Kind: {layer['kind']}")
        if layer['kind'] == 'type':
            st.write(f"Text: {layer['text']}")
        st.write("")
