use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

use unicode_normalization::UnicodeNormalization;

fn mod_init() {
}

fn sme_utils_normalize_caseless_impl(text: &str) -> String {
    text.nfkd().collect::<String>().to_lowercase()
}

#[pyfunction]
pub fn sme_utils_normalize_caseless(text: &str) -> PyResult<String> {
    Ok(sme_utils_normalize_caseless_impl(text))
}

fn sme_utils_is_equal_caseless_impl(left: &str, right: &str) -> bool {
    sme_utils_normalize_caseless_impl(left) == sme_utils_normalize_caseless_impl(right)
}

#[pyfunction]
pub fn sme_utils_is_equal_caseless(left: &str, right: &str) -> PyResult<bool> {
    Ok(sme_utils_is_equal_caseless_impl(left, right))
}

fn sme_utils_shellwords_impl(text: &str) -> Vec<String> {
    match shell_words::split(text) {
        Ok(words) => words,
        Err(_) => Vec::new()
    }
}

#[pyfunction]
pub fn sme_utils_shellwords(text: &str) -> PyResult<Vec<String>> {
    Ok(sme_utils_shellwords_impl(text))
}

pub fn sme_utils_pymodule(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    mod_init();

    m.add_wrapped(wrap_pyfunction!(sme_utils_normalize_caseless))?;
    m.add_wrapped(wrap_pyfunction!(sme_utils_is_equal_caseless))?;
    m.add_wrapped(wrap_pyfunction!(sme_utils_shellwords))?;

    Ok(())
}
