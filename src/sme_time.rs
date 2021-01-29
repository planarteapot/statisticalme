use pyo3::prelude::*;
use pyo3::types::{PyString};
use pyo3::wrap_pyfunction;

use chrono::prelude::*;
use chrono::{DateTime, Utc};

static _TIMEFMT: &str = "%Y-%m-%d %H:%M:%S %Z%z";

pub fn mod_init() {
}

#[pyfunction]
pub fn sme_time_now() -> PyResult<u32> {
    Ok(Utc::now().timestamp() as u32)
}

fn sme_time_as_string_impl(time_ob: u32) -> String {
    Utc.timestamp(time_ob as i64, 0).format(_TIMEFMT).to_string()
}

#[pyfunction]
pub fn sme_time_as_string(time_ob: u32) -> PyResult<String> {
    Ok(sme_time_as_string_impl(time_ob))
}

#[pyfunction]
pub fn sme_time_from_string(time_str: &PyString) -> PyResult<u32> {
    match DateTime::parse_from_str(&time_str.to_string_lossy(), _TIMEFMT) {
        Ok(dt) => Ok(dt.timestamp() as u32),
        Err(_) => Ok(0)
    }
}

pub fn sme_time_pymodule(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(sme_time_now))?;
    m.add_wrapped(wrap_pyfunction!(sme_time_as_string))?;
    m.add_wrapped(wrap_pyfunction!(sme_time_from_string))?;

    Ok(())
}
