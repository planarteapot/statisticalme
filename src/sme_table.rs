use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

use cli_table::{
    format::{Border, HorizontalLine, Justify, Padding, Separator, VerticalLine},
    Cell, Table,
};
use termcolor::ColorChoice;

// fn mod_init() {
// }

fn sme_table_render_impl(
    header: &Vec<String>,
    data_align: &Vec<String>,
    data: &Vec<Vec<String>>,
) -> Vec<String> {
    let mut table_cells = Vec::new();

    for drow in data {
        let mut row_cells = Vec::new();

        for (dcell, djust) in drow.iter().zip(data_align.iter()) {
            row_cells.push(
                dcell
                    .cell()
                    .justify(if djust.eq("l") {
                        Justify::Left
                    } else {
                        Justify::Right
                    })
                    .padding(Padding::builder().build()),
            )
        }

        table_cells.push(row_cells)
    }

    table_cells
        .table()
        .color_choice(ColorChoice::Never)
        .title(header)
        .border(Border::builder().build())
        .separator(
            Separator::builder()
                .title(Some(HorizontalLine::new(' ', ' ', ' ', '-')))
                .column(Some(VerticalLine::new(' ')))
                .build(),
        )
        .display()
        .unwrap()
        .to_string()
        .split("\n")
        .map(|n| n.to_string())
        .collect()
}

#[pyfunction]
pub fn sme_table_render(
    header: Vec<String>,
    data_align: Vec<String>,
    data: Vec<Vec<String>>,
) -> PyResult<Vec<String>> {
    Ok(sme_table_render_impl(&header, &data_align, &data))
}

pub fn sme_table_pymodule(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // mod_init();

    m.add_wrapped(wrap_pyfunction!(sme_table_render))?;

    Ok(())
}
