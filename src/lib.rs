mod sme_time;
mod sme_utils;

use pyo3::prelude::*;
// use pyo3::wrap_pyfunction;

// fn mod_init() {
// }

#[pymodule]
fn statisticalme(py: Python, m: &PyModule) -> PyResult<()> {
    // mod_init();

    sme_time::sme_time_pymodule(py, m)?;
    sme_utils::sme_utils_pymodule(py, m)?;

    Ok(())
}
