mod sme_time;

use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[pyfunction]
fn library_init() {
    sme_time::mod_init();
}

#[pymodule]
fn statisticalme(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(library_init))?;

    sme_time::sme_time_pymodule(py, m)?;

    Ok(())
}
