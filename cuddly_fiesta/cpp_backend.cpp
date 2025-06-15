#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>

namespace py = pybind11;

std::vector<double> raised_cosine_window(std::size_t n) {
    std::vector<double> w(n);
    std::vector<double> w(n);
    if (n == 0) return w;
    if (n == 1) {
        w[0] = 0.0; 
        return w;
    }
    for (std::size_t i = 0; i < n; ++i) {
        double t = -M_PI / 2.0 + (static_cast<double>(i) / (n - 1)) * M_PI;
        w[i] = 0.5 * (1.0 + std::sin(t));
    }
    return w;
}

py::array_t<double> generate_p_wave(py::array_t<double> t_norm, double amplitude) {
    py::buffer_info buf = t_norm.request();
    std::size_t n = static_cast<std::size_t>(buf.shape[0]);
    double* t = static_cast<double*>(buf.ptr);
    auto result = py::array_t<double>(n);
    auto res = result.mutable_unchecked<1>();

    const double ra_center = 0.32;
    const double ra_width = 0.10;
    const double ra_peak_fraction = 0.42;
    const double la_center = 0.68;
    const double la_width = 0.22;
    const double la_peak_fraction = 0.48;

    double max_val = 0.0;
    for (std::size_t i = 0; i < n; ++i) {
        double ra = ra_peak_fraction * amplitude * std::exp(-0.5 * std::pow((t[i] - ra_center) / ra_width, 2));
        double la = la_peak_fraction * amplitude * std::exp(-0.5 * std::pow((t[i] - la_center) / la_width, 2));
        double val = ra + la;
        res(i) = val;
        double absv = std::abs(val);
        if (absv > max_val) max_val = absv;
    }
    if (max_val > 0.0) {
        for (std::size_t i = 0; i < n; ++i) {
            res(i) = res(i) * (amplitude / max_val);
        }
    }

    std::size_t n_win = std::max<std::size_t>(1, n / 10);
    if (n_win < n / 2) {
        auto onset = raised_cosine_window(n_win);
        for (std::size_t i = 0; i < n_win; ++i) {
            res(i) *= onset[i];
            res(n - 1 - i) *= onset[i];
        }
    }
    return result;
}

PYBIND11_MODULE(cpp_backend, m) {
    m.def("generate_p_wave", &generate_p_wave, "Generate P-wave morphology",
          py::arg("t_norm"), py::arg("amplitude"));
}

