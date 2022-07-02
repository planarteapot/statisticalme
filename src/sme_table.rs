use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

use cli_table::{
    format::{Border, Separator},
    Table,
};
use termcolor::ColorChoice;

// fn mod_init() {
// }

fn sme_table_render_impl(
    header: &Vec<String>,
    data: &Vec<Vec<String>>,
) -> Vec<String> {
    let tt = data
        .table()
        .color_choice(ColorChoice::Never)
        .title(header)
        .border(Border::builder().build())
        .separator(Separator::builder().build());

    tt.display()
        .unwrap()
        .to_string()
        .split("\n")
        .map(|n| n.to_string())
        .collect()
}

#[pyfunction]
pub fn sme_table_render(
    header: Vec<String>,
    data: Vec<Vec<String>>,
) -> PyResult<Vec<String>> {
    Ok(sme_table_render_impl(&header, &data))
}

pub fn sme_table_pymodule(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    // mod_init();

    m.add_wrapped(wrap_pyfunction!(sme_table_render))?;

    Ok(())
}
