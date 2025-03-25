from tabulate import tabulate
from textwrap import wrap

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
        ##############################
        print(section("Project info"))

        print(paragraph("Title"))
        print(self.project.info.title)

        print(paragraph("Description"))
        print('\n'.join(wrap(self.project.info.description, width=60)))

        #######################################
        print(section("Crystallographic data"))
        for model in self.project.sample_models._models.values():
            print(paragraph("Phase datablock"))
            print(f'🧩 {model.model_id}')

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

        #############################
        print(section("Experiments"))
        for expt in self.project.experiments._experiments.values():
            print(paragraph("Experiment datablock"))
            print(f'🔬 {expt.id}')

            print(paragraph("Experiment type"))
            print(f'{expt.expt_type.diffr_mode}, {expt.expt_type.radiation_probe}, {expt.expt_type.expt_mode}')

            print(paragraph("Wavelength"))
            print(expt.instr_setup.wavelength.value)

            print(paragraph("2θ offset"))
            print(expt.instr_calib.twotheta_offset.value)

            print(paragraph("Profile type"))
            print(expt.peak_profile.profile_type)

            print(paragraph("Peak broadening (Gaussian)"))
            print(tabulate([
                ["U", expt.peak_broad.gauss_u.value],
                ["V", expt.peak_broad.gauss_v.value],
                ["W", expt.peak_broad.gauss_w.value]
            ], headers=["Parameter", "Value"], tablefmt="fancy_outline"))

            print(paragraph("Peak broadening (Lorentzian)"))
            print(tabulate([
                ["X", expt.peak_broad.lorentz_x.value],
                ["Y", expt.peak_broad.lorentz_y.value]
            ], headers=["Parameter", "Value"], tablefmt="fancy_outline"))

        ############################
        print(section("Refinement"))

        print(paragraph("Calculation engine"))
        print(self.project.analysis.current_calculator)

        print(paragraph("Minimization engine"))
        print(self.project.analysis.current_minimizer)

        print(paragraph("Fit quality"))
        fit_metrics = [
            ["Goodness-of-fit (reduced χ²)", f"{self.project.analysis.fit_results.reduced_chi_square:.2f}"]
        ]
        print(tabulate(fit_metrics, tablefmt="fancy_outline"))

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