import os
import tempfile
import streamlit as st
from psd_tools import PSDImage

def has_multiple_artboards(psd_file):
    psd = PSDImage.open(psd_file)
    for layer in psd:
        if isinstance(layer, psd_tools.api.layers.Artboard):
            return True
    return False

def select_artboard(psd_file):
    psd = PSDImage.open(psd_file)
    artboard_names = [f"Artboard {i+1}" for i in range(len(list(filter(lambda x: isinstance(x, psd_tools.api.layers.Artboard), psd))))]
    selected_artboard = st.selectbox("Select Artboard:", artboard_names)
    return selected_artboard


def separate_parts(psd_file, artboard=None):
    psd = PSDImage.open(psd_file)
    if artboard:
        psd = artboard
    output_dir = tempfile.mkdtemp()
    layer_info = []  # List to store layer information
    layer_order = 0  # Initialize layer order

    for i, layer in enumerate(psd):
        if layer.is_visible():
            layer_order += 1  # Increment layer order
            if layer.is_group():
                # Flatten the group into a single PNG
                group_img = layer.composite()
                group_img.save(os.path.join(output_dir, f'{layer.name}.png'))
                # Add group info to layer_info
                x, y, width, height = layer.bbox
                top_left_x = x
                top_left_y = y
                width = width - x
                height = height - y
                layer_info.append({
                    'name': layer.name,
                    'x': top_left_x,
                    'y': top_left_y,
                    'width': width,
                    'height': height,
                    'kind': layer.kind,
                    'order': layer_order,
                    'blend_mode': layer.blend_mode  # Add blending mode
                })
            else:
                process_layer(layer, output_dir, layer_order, layer_info)

    return output_dir, layer_info, psd.width, psd.height

def process_layer(layer, output_dir, layer_order, layer_info):
    # Get blending mode of the layer
    blending_mode = layer.blend_mode
    if layer.kind == 'type':
        # Skip exporting type layers
        text_info = {
            'name': layer.name,
            'bbox': layer.bbox,
            'kind': layer.kind,
            'text': layer.text,
            'order': layer_order,  # Add layer order
            'style_sheet': layer.engine_dict.get('StyleRun', []),
            'font_list': layer.resource_dict.get('FontSet', []),
            'blend_mode': blending_mode,  # Add blending mode
            'layer_effects': layer.effects  # Add layer effects
        }
        layer_info.append(text_info)
    else:
        # Export all other layers as PNG
        img = layer.composite()
        img.save(os.path.join(output_dir, f'{layer.name}.png'))
        # Retain metadata for non-type layers
        x, y, width, height = layer.bbox
        # Calculate top-left corner coordinates and width-height
        top_left_x = x
        top_left_y = y
        width = width - x
        height = height - y
        layer_info.append({
            'name': layer.name,
            'x': top_left_x,
            'y': top_left_y,
            'width': width,
            'height': height,
            'kind': layer.kind,
            'order': layer_order,
            'blend_mode': blending_mode  # Add blending mode
        })

# Streamlit UI code
st.title("PSD Importer Prototype")
st.caption("This extracts visible layers, converts all non-images to PNG, outputs text, and tells us the location on the canvas for each exported part")

uploaded_file = st.file_uploader("Upload a PSD file", type=["psd"])

if uploaded_file is not None:
    if has_multiple_artboards(uploaded_file):
        selected_artboard = select_artboard(uploaded_file)
        output_dir, layer_info, canvas_width, canvas_height = separate_parts(uploaded_file, selected_artboard)
    else:
        output_dir, layer_info, canvas_width, canvas_height = separate_parts(uploaded_file)

    st.write("Canvas Width:", canvas_width)
    st.write("Canvas Height:", canvas_height)
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
        if 'x' in layer and 'y' in layer and 'width' in layer and 'height' in layer:
            st.write(f"Top Left Corner (x, y): ({layer['x']}, {layer['y']})")
            st.write(f"Width: {layer['width']}")
            st.write(f"Height: {layer['height']}")
        st.write(f"Kind: {layer['kind']}")
        if layer['kind'] == 'type':
            st.write(f"Text: {layer['text']}")
            st.write(f"StyleRun: {layer['style_sheet']}")
            st.write(f"Font List: {layer['font_list']}")
            st.write(f"Layer Effects: {layer['layer_effects']}")
        # Print blending mode
        st.write(f"Blending Mode: {layer.get('blend_mode', 'Normal')}")
        st.write(f"Order: {layer['order']}")
        st.write("")
