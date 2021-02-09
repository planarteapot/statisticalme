use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

// use chrono::prelude::*;
use chrono::{NaiveDateTime, Utc, TimeZone, Offset, LocalResult};
use chrono_tz::Tz;

static _TIMEFMT: &str = "%Y-%m-%d %H:%M:%S";
static _TIMEFMTSHORT: &str = "%a %H:%M";

pub fn mod_init() {
}

#[derive(PartialEq, Debug)]
pub struct SmeAsTzResult {
    time_str: String,
    sorting_factor: i32,
    valid: bool,
}

pub fn sme_time_now_impl() -> u32 {
    Utc::now().timestamp() as u32
}

#[pyfunction]
pub fn sme_time_now() -> PyResult<u32> {
    Ok(sme_time_now_impl())
}

fn sme_time_as_string_impl(time_ob: u32) -> String {
    Utc.timestamp(time_ob as i64, 0).format(_TIMEFMT).to_string()
}

#[pyfunction]
pub fn sme_time_as_string(time_ob: u32) -> PyResult<String> {
    Ok(sme_time_as_string_impl(time_ob))
}

fn sme_time_from_string_impl(time_str: &str) -> u32 {
    match NaiveDateTime::parse_from_str(&time_str[..19], _TIMEFMT) {
        Ok(dt) => dt.timestamp() as u32,
        Err(_) => 0
    }
}

#[pyfunction]
pub fn sme_time_from_string(time_str: &str) -> PyResult<u32> {
    Ok(sme_time_from_string_impl(time_str))
}

pub fn sme_time_is_valid_timezone_impl(tz_str: &str) -> bool {
    match tz_str.parse::<Tz>() {
        Ok(_) => true,
        Err(_) => {
            if tz_str.len() >= 4 {
                let prefix = tz_str[..3].to_lowercase();

                match prefix.as_str() {
                    "utc" | "gmt" => tz_str[3..].parse::<f32>().is_ok(),
                    "fof" => tz_str[3..].parse::<i32>().is_ok(),
                    _ => false
                }
            } else {
                false
            }
        }
    }
}

#[pyfunction]
pub fn sme_time_is_valid_timezone(tz_str: &str) -> PyResult<bool> {
    Ok(sme_time_is_valid_timezone_impl(tz_str))
}

fn format_tz_result(time_str: &String, sorting_factor: i32) -> String {
    format!("{}{},{}", &time_str[..2], &time_str[3..], sorting_factor)
}

pub fn sme_time_convert_to_timezone_impl(time_ob: u32, tz_str: &str) -> Option<String> {
    match tz_str.parse::<Tz>() {
        Ok(tz) => {
            let dt = match Utc.timestamp_opt(time_ob as i64, 0) {
                LocalResult::Single(sdt) => Some(sdt),
                LocalResult::Ambiguous(adt, _) => Some(adt),
                _ => None
            }?.with_timezone(&tz);

            Some(format_tz_result(&dt.format(_TIMEFMTSHORT).to_string(), dt.offset().fix().local_minus_utc()))
        },
        Err(_) => {
            if tz_str.len() >= 4 {
                let prefix = tz_str[..3].to_lowercase();

                let offset: i32 = match prefix.as_str() {  // seconds
                    "utc" | "gmt" => Some(tz_str[3..].parse::<i32>().ok()? * 3600_i32),
                    "fof" => Some(tz_str[3..].parse::<i32>().ok()? * 60_i32),
                    _ => None
                }?;

                match offset {
                    // Check the offset in seconds is within -12hr ... 12hr
                    -43200..=43200 => {
                        let dt = match Utc.timestamp_opt(time_ob as i64 + offset as i64, 0) {
                            LocalResult::Single(sdt) => Some(sdt),
                            LocalResult::Ambiguous(adt, _) => Some(adt),
                            _ => None
                        }?;

                        Some(format_tz_result(&dt.format(_TIMEFMTSHORT).to_string(), offset))
                    },
                    _ => None
                }
            } else {
                None
            }
        }
    }
}

#[pyfunction]
pub fn sme_time_convert_to_timezone(time_ob: u32, tz_str: &str) -> PyResult<String> {
    Ok(match sme_time_convert_to_timezone_impl(time_ob, tz_str) {
        Some(res) => res,
        None => "".to_string()
    })
}

pub fn sme_time_pymodule(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(sme_time_now))?;
    m.add_wrapped(wrap_pyfunction!(sme_time_as_string))?;
    m.add_wrapped(wrap_pyfunction!(sme_time_from_string))?;
    m.add_wrapped(wrap_pyfunction!(sme_time_is_valid_timezone))?;
    m.add_wrapped(wrap_pyfunction!(sme_time_convert_to_timezone))?;

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

    #[test]
    fn test_sme_time_is_valid_timezone_succeed() {
        assert!(sme_time_is_valid_timezone_impl("America/New_York"));
    }

    #[test]
    fn test_sme_time_is_valid_timezone_fail() {
        assert!(!sme_time_is_valid_timezone_impl("MiddleEarth/Hobbiton"));
    }

    #[test]
    fn test_sme_time_convert_to_timezone_tz_succeed() {
        assert_eq!(sme_time_convert_to_timezone_impl(1608594507_u32, "America/New_York"), Some("Mo 18:48,-18000".to_string()))
    }

    #[test]
    fn test_sme_time_convert_to_timezone_offs_succeed() {
        assert_eq!(sme_time_convert_to_timezone_impl(1608594507_u32, "utc-5"), Some("Mo 18:48,-18000".to_string()))
    }
}
