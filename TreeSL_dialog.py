from qgis.PyQt.QtWidgets import (
    QAction, QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QLineEdit, QHBoxLayout, QScrollArea, QSizePolicy, QWidget
)
from qgis.core import (
    QgsVectorLayer, QgsField, QgsFeature, QgsVectorDataProvider, QgsProject
)
from qgis.utils import iface
from PyQt5.QtCore import QVariant


class TreeSLPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_menu = None

    def initGui(self):
        # Create action for plugin
        self.plugin_menu = QAction("TreeSL Plugin", self.iface.mainWindow())
        self.plugin_menu.triggered.connect(self.run)
        iface.addPluginToMenu("&TreeSL Plugin", self.plugin_menu)

    def unload(self):
        iface.removePluginMenu("&TreeSL Plugin", self.plugin_menu)

    def run(self):
        # Open dialog to load layers and process data
        dialog = TreeSLDialog()
        dialog.exec_()


class TreeSLDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tree Plantation Suitability")
        self.resize(500, 400)  # Set a reasonable default size

        # Main Layout
        main_layout = QVBoxLayout()

        # Instructions with styling
        instruction_label = QLabel("Load layers for Rainfall, Soil, and Land Use.")
        instruction_label.setStyleSheet("color: darkblue; font-weight: bold; font-size: 14px;")
        main_layout.addWidget(instruction_label)

        # Scroll Area for Layer Inputs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Layer input fields
        self.rainfall_input = self.create_layer_input("Rainfall Layer", self.load_rainfall_layer)
        self.soil_input = self.create_layer_input("Soil Layer", self.load_soil_layer)
        self.land_use_input = self.create_layer_input("Land Use Layer", self.load_land_use_layer)

        # Add rows to scrollable layout
        scroll_layout.addLayout(self.rainfall_input)
        scroll_layout.addLayout(self.soil_input)
        scroll_layout.addLayout(self.land_use_input)

        scroll_area.setWidget(scroll_widget)

        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)

        # Add stretch to push buttons to the bottom
        main_layout.addStretch()

        # Process and Cancel buttons in the same row at the bottom
        button_layout = QHBoxLayout()

        # Process button with styling
        self.process_button = QPushButton("Process Suitability")
        self.process_button.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        self.process_button.clicked.connect(self.process_suitability)
        button_layout.addWidget(self.process_button)

        # Cancel button with styling
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.cancel_button.clicked.connect(self.reject)  # Close the dialog when clicked
        button_layout.addWidget(self.cancel_button)

        # Add button layout to main layout
        main_layout.addLayout(button_layout)

        # Set main layout
        self.setLayout(main_layout)

        # Layer variables
        self.rainfall_layer = None
        self.soil_layer = None
        self.land_use_layer = None

    def create_layer_input(self, label_text, load_function):
        """Create a row for loading layers with a label, text box, and browse button."""
        row_layout = QHBoxLayout()

        # Label with styling
        label = QLabel(label_text)
        label.setStyleSheet("color: darkgreen; font-size: 12px; font-weight: bold;")
        row_layout.addWidget(label)

        # Text Box (for displaying file path)
        text_box = QLineEdit()
        text_box.setPlaceholderText(f"Select {label_text.lower()}...")
        text_box.setReadOnly(True)
        text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        text_box.setStyleSheet("background-color: #f0f0f0;")
        row_layout.addWidget(text_box)

        # Browse Button with styling
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(lambda: self.load_file(text_box, load_function))
        browse_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        browse_button.setStyleSheet("background-color: orange; color: black; font-weight: bold;")
        row_layout.addWidget(browse_button)

        # Consistent styling and layout
        row_layout.setContentsMargins(10, 5, 10, 5)
        return row_layout

    def load_file(self, text_box, load_function):
        """Open file dialog and load the selected layer."""
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Layer", "", "Shapefiles (*.shp)")
        if filepath:
            text_box.setText(filepath)
            load_function(filepath)

    def load_rainfall_layer(self, filepath):
        self.rainfall_layer = QgsVectorLayer(filepath, "Rainfall", "ogr")
        QgsProject.instance().addMapLayer(self.rainfall_layer)

    def load_soil_layer(self, filepath):
        self.soil_layer = QgsVectorLayer(filepath, "Soil", "ogr")
        QgsProject.instance().addMapLayer(self.soil_layer)

    def load_land_use_layer(self, filepath):
        self.land_use_layer = QgsVectorLayer(filepath, "Land Use", "ogr")
        QgsProject.instance().addMapLayer(self.land_use_layer)

    def process_suitability(self):
        if not self.rainfall_layer or not self.soil_layer or not self.land_use_layer:
            iface.messageBar().pushMessage("Error", "Please load all required layers.", level=3)  # Qgis.Critical
            return

        # Create output layer
        suitable_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "Suitable Areas", "memory")
        dp = suitable_layer.dataProvider()
        dp.addAttributes([QgsField("Tree_Type", QVariant.String), QgsField("Suitability", QVariant.String)])
        suitable_layer.updateFields()

        # Dummy logic for suitability
        for feature in self.rainfall_layer.getFeatures():
            if 600 <= feature['Rainfall'] <= 1500:  # Example condition
                new_feature = QgsFeature()
                new_feature.setGeometry(feature.geometry())
                new_feature.setAttributes(["General Tree", "High"])
                dp.addFeature(new_feature)

        QgsProject.instance().addMapLayer(suitable_layer)
        iface.messageBar().pushMessage("Success", "Tree suitability layer generated!", level=1)  # Qgis.Success
