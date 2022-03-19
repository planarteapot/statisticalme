use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

// use lazy_static::lazy_static;
use psutil;

fn mod_init() {}

pub fn sme_pstat_cpumem_percent_impl() -> (f32, f32) {
    // lazy_static! {
    //     static mut PERSISTANT_CPU = psutil::cpu::CpuPercentCollector::new();
    // }

    let cpuper: f32 = match psutil::cpu::CpuPercentCollector::new() {
        Ok(mut pers_cpu) => match pers_cpu.cpu_percent() {
            Ok(perc) => perc,
            _ => 0.0,
        },
        _ => 0.0,
    };

    let memper: f32 = match psutil::memory::virtual_memory() {
        Ok(memobj) => memobj.percent(),
        _ => 0.0,
    };

    (cpuper, memper)
}

#[pyfunction]
pub fn sme_pstat_cpumem_percent() -> PyResult<(f32, f32)> {
    Ok(sme_pstat_cpumem_percent_impl())
}

pub fn sme_pstat_pymodule(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    mod_init();

    m.add_wrapped(wrap_pyfunction!(sme_pstat_cpumem_percent))?;

    Ok(())
}
