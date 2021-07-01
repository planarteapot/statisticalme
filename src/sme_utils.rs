use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

use unicase::UniCase;

fn mod_init() {
}

// def normalize_caseless(text):
//     return unicodedata.normalize("NFKD", text.casefold())
fn sme_utils_normalize_caseless_impl(text: &str) -> String {
    UniCase::new(text).to_string()
}

#[pyfunction]
pub fn sme_utils_normalize_caseless(text: &str) -> PyResult<String> {
    Ok(sme_utils_normalize_caseless_impl(text))
}

// def is_equal_caseless(left, right):
//     return normalize_caseless(left) == normalize_caseless(right)
fn sme_utils_is_equal_caseless_impl(left: &str, right: &str) -> bool {
    sme_utils_normalize_caseless_impl(left) == sme_utils_normalize_caseless_impl(right)
}

#[pyfunction]
pub fn sme_utils_is_equal_caseless(left: &str, right: &str) -> PyResult<bool> {
    Ok(sme_utils_is_equal_caseless_impl(left, right))
}

pub fn sme_utils_pymodule(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    mod_init();

    m.add_wrapped(wrap_pyfunction!(sme_utils_normalize_caseless))?;
    m.add_wrapped(wrap_pyfunction!(sme_utils_is_equal_caseless))?;

    Ok(())
}
