use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

use chrono::prelude::*;
use chrono::{NaiveDateTime, Utc};

static _TIMEFMT: &str = "%Y-%m-%d %H:%M:%S";

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

fn sme_time_from_string_impl(time_str: &str) -> u32 {
    match NaiveDateTime::parse_from_str(&time_str[0..19], _TIMEFMT) {
        Ok(dt) => dt.timestamp() as u32,
        Err(_) => 0
    }
}

#[pyfunction]
pub fn sme_time_from_string(time_str: &str) -> PyResult<u32> {
    Ok(sme_time_from_string_impl(time_str))
}

pub fn sme_time_pymodule(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(sme_time_now))?;
    m.add_wrapped(wrap_pyfunction!(sme_time_as_string))?;
    m.add_wrapped(wrap_pyfunction!(sme_time_from_string))?;

    Ok(())
}

#[cfg(test)]
mod sme_time_tests {
    use super::*;

    #[test]
    fn test_sme_time_as_string() {
        assert_eq!(sme_time_as_string_impl(1608594507_u32), "2020-12-21 23:48:27");
    }

    #[test]
    fn test_sme_time_from_string() {
        let dtstamp = sme_time_from_string_impl("2020-12-21 23:48:26");
        assert_eq!(dtstamp, 1608594506_u32);
    }
}
