# summary.py                                                     # Reporting and results export

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
        print("===== Project Report =====")
        print(f"Title: {self.project.info.title}")
        print(f"Description: {self.project.info.description}")
        print("\n--- Sample Models ---")
        self.project.sample_models.show_params()

        print("\n--- Experiments ---")
        self.project.experiments.show_params()

        print("\n--- Analysis ---")
        self.project.analysis.show_fit_results()

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