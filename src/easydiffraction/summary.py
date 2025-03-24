from tabulate import tabulate

from easydiffraction.utils.utils import paragraph, section


class Summary:
    """
    Generates reports and exports results from the project.
    
    This class collects and presents all relevant information
    about the refined model, experiments, and analysis results.
    """

    def __init__(self, project):
        """
        Initialize the summary with a reference to the project.

        :param project: The Project instance this summary belongs to.
        """
        self.project = project

    # ------------------------------------------
    #  Report Generation
    # ------------------------------------------

    def show_report(self):
        """
        Show a report of the entire analysis process, including:
        - Project metadata
        - Sample models and parameters
        - Experiment configurations and results
        - Analysis and refinement results
        """
        print(section("Project info"))

        print(paragraph("Title"))
        print(self.project.info.title)

        print(paragraph("Description"))
        print(self.project.info.description)

        print(section("Crystallographic data"))
        for model in self.project.sample_models._models.values():
            print(paragraph("Phase datablock"))
            print(model.id)

            print(paragraph("Space group"))
            print(model.space_group.name)

            print(paragraph("Cell parameters"))
            cell_data = [[k.replace('length_', '').replace('angle_', ''), f"{v:.4f}"] for k, v in model.cell.as_dict().items()]
            print(tabulate(cell_data, headers=["Parameter", "Value"], tablefmt="fancy_outline"))

            print(paragraph("Atom sites"))
            atom_table = []
            for site in model.atom_sites:
                fract_x = site.fract_x.value
                fract_y = site.fract_y.value
                fract_z = site.fract_z.value
                b_iso = site.b_iso.value
                atom_table.append([
                    site.label, site.type_symbol,
                    f"{fract_x:.4f}", f"{fract_y:.4f}", f"{fract_z:.4f}",
                    site.occupancy,
                    f"{b_iso:.4f}"
                ])
            headers = ["Label", "Type", "fract_x", "fract_y", "fract_z", "Occupancy", "B_iso"]
            print(tabulate(atom_table, headers=headers, tablefmt="fancy_outline"))

        print(section("Experiments"))
        self.project.experiments.show_params()

        print(section("Analysis"))
        print("Bla bla bla")
        #self.project.analysis.show_fit_results()

    # ------------------------------------------
    #  Exporting
    # ------------------------------------------

    def as_cif(self) -> str:
        """
        Export the final refined data and analysis results as CIF format.
        
        Includes project info, sample models, experiment data, and refined parameters.
        """
        cif_data = (
            self.project.info.as_cif() +
            self.project.sample_models.as_cif() +
            self.project.experiments.as_cif() +
            self.project.analysis.as_cif()
        )
        return cif_data

    def as_html(self) -> str:
        """
        Export the final report as an HTML document (stub).
        """
        html = f"""
        <html>
        <head><title>{self.project.info.title} - Report</title></head>
        <body>
            <h1>{self.project.info.title}</h1>
            <h2>Description</h2>
            <p>{self.project.info.description}</p>

            <h2>Sample Models</h2>
            <pre>{self.project.sample_models.show_params()}</pre>

            <h2>Experiments</h2>
            <pre>{self.project.experiments.show_params()}</pre>

            <h2>Analysis Results</h2>
            <pre>{self.project.analysis.show_fit_results()}</pre>
        </body>
        </html>
        """
        return html