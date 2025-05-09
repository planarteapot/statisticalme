mod sme_table;
mod sme_time;
mod sme_utils;

use pyo3::prelude::*;
// use pyo3::wrap_pyfunction;

// fn mod_init() {
// }

#[pymodule]
fn statisticalme(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // mod_init();

    sme_table::sme_table_pymodule(m)?;
    sme_time::sme_time_pymodule(m)?;
    sme_utils::sme_utils_pymodule(m)?;

    Ok(())
}
