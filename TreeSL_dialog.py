from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QHBoxLayout, QSizePolicy, QComboBox
)
from qgis.core import QgsVectorLayer, QgsProject, QgsProcessingFeatureSourceDefinition
from qgis.utils import iface
import processing

class TreeSLDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Urban Flood Risk Management")
        self.resize(500, 300)

        # Main Layout
        main_layout = QVBoxLayout()

        # Instruction Label
        instruction_label = QLabel("Select a city and load layers from the database for analysis:")
        instruction_label.setStyleSheet("color: darkblue; font-weight: bold; font-size: 14px;")
        main_layout.addWidget(instruction_label)

        # City selection combo box
        self.city_selector = QComboBox()
        self.city_selector.setStyleSheet("font-size: 12px;")
        self.city_selector.addItems(["Blantyre City", "Lilongwe City", "Mzuzu City", "Zomba City"])
        main_layout.addWidget(self.city_selector)

        # Layer input fields
        self.city_layer_input = self.create_layer_input("City Boundary Layer", self.load_city_layer)
        self.river_layer_input = self.create_layer_input("River Layer", self.load_river_layer)
        self.road_layer_input = self.create_layer_input("Main Road Layer", self.load_road_layer)

        # Add rows to main layout
        main_layout.addLayout(self.city_layer_input)
        main_layout.addLayout(self.river_layer_input)
        main_layout.addLayout(self.road_layer_input)

        # Add stretch to push buttons to the bottom
        main_layout.addStretch()

        # Process and Cancel buttons in the same row at the bottom
        button_layout = QHBoxLayout()

        self.process_button = QPushButton("Process Flood Risk")
        self.process_button.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        self.process_button.clicked.connect(self.process_flood_risk)
        button_layout.addWidget(self.process_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.cancel_button.clicked.connect(self.reject)  # Close the dialog when clicked
        button_layout.addWidget(self.cancel_button)

        # Add button layout to main layout
        main_layout.addLayout(button_layout)

        # Set main layout
        self.setLayout(main_layout)

        # Layer variables
        self.city_layer = None
        self.river_layer = None
        self.road_layer = None

    def create_layer_input(self, label_text, load_function):
        """Create a row for loading layers from the database with a label and text box."""
        row_layout = QHBoxLayout()

        label = QLabel(label_text)
        label.setStyleSheet("color: darkgreen; font-size: 12px; font-weight: bold;")
        row_layout.addWidget(label)

        text_box = QLineEdit()
        text_box.setPlaceholderText(f"Layer from database: {label_text}")
        text_box.setReadOnly(True)
        text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        text_box.setStyleSheet("background-color: #f0f0f0;")
        row_layout.addWidget(text_box)

        load_button = QPushButton("Load")
        load_button.clicked.connect(lambda: load_function(text_box))
        load_button.setStyleSheet("background-color: orange; color: black; font-weight: bold;")
        row_layout.addWidget(load_button)

        return row_layout

    def load_city_layer(self, text_box):
        self.city_layer = self.load_layer_from_database("City Boundary Layer")
        text_box.setText("City Boundary Layer Loaded")

    def load_river_layer(self, text_box):
        self.river_layer = self.load_layer_from_database("River Layer")
        text_box.setText("River Layer Loaded")

    def load_road_layer(self, text_box):
        self.road_layer = self.load_layer_from_database("Main Road Layer")
        text_box.setText("Main Road Layer Loaded")

    def load_layer_from_database(self, layer_name):
        selected_city = self.city_selector.currentText()
        uri = (
            "dbname='postgres' host=localhost port=5432 user='postgres' "
            "password='password' table=\"{}\".\"{}\" (geometry)"
        ).format(selected_city, layer_name)
        layer = QgsVectorLayer(uri, layer_name, "postgres")
        if not layer.isValid():
            iface.messageBar().pushMessage(
                "Error", f"Failed to load {layer_name} for {selected_city}.", level=3
            )
            return None
        QgsProject.instance().addMapLayer(layer)
        iface.messageBar().pushMessage(
            "Success", f"{layer_name} loaded successfully for {selected_city}.", level=1
        )
        return layer

    def process_flood_risk(self):
        if not (self.city_layer and self.river_layer and self.road_layer):
            iface.messageBar().pushMessage("Error", "All layers must be loaded for analysis.", level=3)
            return

        # Ensure all layers use the same CRS
        target_crs = self.city_layer.crs()
        self.river_layer.setCrs(target_crs)
        self.road_layer.setCrs(target_crs)

        # Buffer around rivers (e.g., 50 meters)
        try:
            river_buffer = processing.run("native:buffer", {
                'INPUT': self.river_layer,
                'DISTANCE': 50,
                'SEGMENTS': 5,
                'END_CAP_STYLE': 0,
                'JOIN_STYLE': 0,
                'MITER_LIMIT': 2,
                'DISSOLVE': False,
                'OUTPUT': 'memory:'
            })['OUTPUT']
        except Exception as e:
            iface.messageBar().pushMessage("Error", f"Buffer processing failed: {str(e)}", level=3)
            return

        # Intersect city layer with river buffer
        try:
            flood_risk_areas = processing.run("native:intersection", {
                'INPUT': QgsProcessingFeatureSourceDefinition(self.city_layer.id(), True),
                'OVERLAY': QgsProcessingFeatureSourceDefinition(river_buffer.id(), True),
                'INPUT_FIELDS': [],
                'OVERLAY_FIELDS': [],
                'OUTPUT': 'memory:'
            })['OUTPUT']
        except Exception as e:
            iface.messageBar().pushMessage("Error", f"Intersection processing failed: {str(e)}", level=3)
            return

        # Add the flood risk layer to the project
        QgsProject.instance().addMapLayer(flood_risk_areas)
        iface.messageBar().pushMessage("Success", "Flood risk analysis complete!", level=1)
