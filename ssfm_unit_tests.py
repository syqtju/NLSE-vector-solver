# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 09:28:50 2024

@author: okrarup
"""

from ssfm_functions import *
from scipy.special import airy
from scipy.optimize import fsolve


def gaussian_pulse_with_beta_2_only(time_s: npt.NDArray[float],
                                    duration_s: [float],
                                    amplitude_sqrt_W: [float],
                                    beta2_s2_per_m: [float],
                                    distance_m: [float]) -> npt.NDArray[complex]:
    """
    Analytical solution for propagating a Gaussian pulse through a fiber with
    only 2nd order dispersion. Useful for unit-testing and comparing
    with numerical results.

    Parameters
    ----------
    time_s : npt.NDArray[float]
        Time in seconds.
    duration_s : [float]
        Duration of Gaussian pulse in seconds.
    amplitude_sqrt_W : [float]
        Gaussian pulse amplitude in sqrt(W).
    beta2_s2_per_m : [float]
        Fiber dispersion in s^2/m.
    distance_m : [float]
        Fiber length in m.

    Returns
    -------
    npt.NDArray[complex]
        Gaussian pulse after propagating distance_m through fiber with beta_2.

    """

    sigma = np.sqrt(duration_s**2- 1j*beta2_s2_per_m*distance_m)

    front_factor = duration_s/sigma
    exponential_factor = np.exp(-0.5*(time_s/sigma)**2)

    return amplitude_sqrt_W*front_factor*exponential_factor


def gaussian_pulse_with_beta_3_only(time_s: npt.NDArray[float],
                                    duration_s: [float],
                                    amplitude_sqrt_W: [float],
                                    beta3_s3_per_m: [float],
                                    distance_m: [float]) -> npt.NDArray[complex]:
    """
    Analytical solution for propagating a Gaussian pulse through a fiber with
    only 3rd order dispersion. Useful for unit-testing and comparing
    with numerical results.

    Parameters
    ----------
    time_s : npt.NDArray[float]
        Time in seconds.
    duration_s : [float]
        Duration of Gaussian pulse in seconds.
    amplitude_sqrt_W : [float]
        Gaussian pulse amplitude in sqrt(W).
    beta3_s3_per_m : [float]
        Fiber dispersion in s^3/m.
    distance_m : [float]
        Fiber length in m.

    Returns
    -------
    npt.NDArray[complex]
        Gaussian pulse after propagating distance_m through fiber with beta_3.

    """
    p = duration_s/np.sqrt(2)
    b = beta3_s3_per_m*distance_m/(2*p**3.0)

    front_factor = 2*np.sqrt(np.pi)/np.abs(b)**(1.0/3.0)
    exponential_factor = np.exp( (2*p-3*b*time_s)/(3*p*b**2) )

    airy_arg = (p-b*time_s)/(p*np.abs(b)**(4.0/3.0))

    airy_output = airy(airy_arg)[0]




    return amplitude_sqrt_W*front_factor*exponential_factor*airy_output


def self_steepening_pulse(time_freq: TimeFreq,
                          duration_s: [float],
                          amplitude_sqrt_W: [float],
                          gamma_per_W_m: [float],
                          distance_m: [float])-> npt.NDArray[complex]:

    w0 = time_freq.center_frequency_Hz*2*np.pi
    s=1/w0/duration_s

    tau = time_freq.t/duration_s
    P_max = amplitude_sqrt_W**2
    L_NL = 1/gamma_per_W_m/P_max

    Z = distance_m/L_NL
    print(s)
    print(f"{Z = }")
    def f(I,tau=tau,s=s,Z=Z):
        return np.exp(-(tau - 3*s*I*Z)**2)-I


    #I_0=pd.read_csv("SS.csv")
    I_0 = np.exp(-0.5*tau**2)

    print("Starting fsolve")
    I_sol=fsolve(f,I_0)

    # SS_df = pd.DataFrame(I_sol)
    # SS_df.to_csv("SS.csv", index=False)

    # tau_df = pd.DataFrame(tau)
    # tau_df.to_csv("tau.csv", index=False)

    return I_sol




def run_all_unit_tests(show_plot_flag = False):



    print("  ")
    print("Running all unit tests !!! ")
    print("  ")
    unit_tests_dispersion(show_plot_flag=show_plot_flag)
    unit_test_nonlinear(show_plot_flag=show_plot_flag)
    print("  ")
    print("All unit tests succeeded!!! ")
    print("  ")


def unit_tests_dispersion(show_plot_flag=False):

    unit_test_beta2(show_plot_flag=show_plot_flag)
    unit_test_beta3(show_plot_flag=show_plot_flag)

def unit_test_beta2(show_plot_flag=False):
    """
    Unit test comparing the theoretical and numerical effects of dispersion
    with negative beta2 on a Gaussian puls.

    Parameters
    ----------
    show_plot_flag : Bool, optional
        Flag to toggle shoing graph comparing theoretical to numerical results.
        The default is False.

    Returns
    -------
    None.

    """
    print("  ")
    print("Doing unit test for dispersion with beta2 only!")
    os.chdir(os.path.realpath(os.path.dirname(__file__)))

    N = 2 ** 15  # Number of points
    dt = 100e-15  # Time resolution [s]

    center_freq_test = FREQ_1550_NM_Hz  # FREQ_CENTER_C_BAND_HZ
    time_freq_test = TimeFreq(N,
                              dt,
                              center_freq_test,
                              describe_time_freq_flag=False)

    # Set up signal
    test_FFT_tol = 1e-3
    test_amplitude = 10.0
    test_pulse_type = "gaussian"
    test_amplitude = 0.25
    test_duration_s = 12e-12

    alpha_test = 0  # dB/m
    beta_list = [-10.66e-26]  # [s^2/m,s^3/m,...]  s^(entry+2)/m
    gamma_test = 0  # 1/W/m
    length_test = 12e3  # m
    number_of_steps = 2**10

    fiber_test = FiberSpan(
        length_test,
        number_of_steps,
        gamma_test,
        beta_list,
        alpha_test,
        use_self_steepening=False,
        describe_fiber_flag=False)

    fiber_list = [fiber_test]  # ,fiber_test_2
    fiber_link = FiberLink(fiber_list)



    test_input_signal = InputSignal(time_freq_test,
                                    test_duration_s,
                                    test_amplitude,
                                    test_pulse_type,
                                    FFT_tol=test_FFT_tol,
                                    describe_input_signal_flag=False)


    exp_name = f"unit_test_beta2"
    # Run SSFM
    ssfm_result_list = SSFM(
        fiber_link,
        test_input_signal,
        show_progress_flag=False,
        experiment_name=exp_name,
        FFT_tol=test_FFT_tol
    )
    final_pulse = ssfm_result_list[0].pulse_matrix[-1,:]
    theoretical_final_pulse = gaussian_pulse_with_beta_2_only(time_freq_test.t,
                                    test_duration_s,
                                    test_amplitude, beta_list[0],
                                    length_test)


    if show_plot_flag:
        fig,ax=plt.subplots(dpi=300)
        #ax.plot(time_freq_test.t/1e-9,get_power(test_input_signal.pulse_field),label = "Initial pulse")
        ax.plot(time_freq_test.t/1e-9,get_power(final_pulse),label = "Final pulse numerical")
        ax.plot(time_freq_test.t/1e-9,get_power(theoretical_final_pulse),label = "Final pulse theoretical")
        ax.set_xlim(-0.5,0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.3),
            ncol=3,
            fancybox=True,
            shadow=True,
        )
        plt.show()

    normalized_energy_diff = compare_field_energies(final_pulse,
                                                    theoretical_final_pulse)
    assert normalized_energy_diff<7.06e-6, f"""ERROR: Normalized energy
    difference between numerical and theoretical pulses is
    {normalized_energy_diff =}, but it should be less than or equal to 7.06e-6.
    Unit test for dispersion with beta2 only FAILED!!!"""

    print("Unit test for dispersion with beta2 only SUCCEEDED!")
    print("  ")

def unit_test_beta3(show_plot_flag=False):
    """
    Unit test comparing the theoretical and numerical effects of dispersion
    with negative beta3 on a Gaussian puls.

    Parameters
    ----------
    show_plot_flag : Bool, optional
        Flag to toggle shoing graph comparing theoretical to numerical results.
        The default is False.

    Returns
    -------
    None.

    """
    print("  ")
    print("Doing unit test for dispersion with beta3 only!")
    os.chdir(os.path.realpath(os.path.dirname(__file__)))

    N = 2 ** 15  # Number of points
    dt = 100e-15  # Time resolution [s]

    center_freq_test = FREQ_1550_NM_Hz  # FREQ_CENTER_C_BAND_HZ
    time_freq_test = TimeFreq(N,
                              dt,
                              center_freq_test,
                              describe_time_freq_flag=False)

    # Set up signal
    test_FFT_tol = 1e-3
    test_amplitude = 10.0
    test_pulse_type = "gaussian"
    test_amplitude = 0.25
    test_duration_s = 12e-12

    alpha_test = 0  # dB/m
    beta_list = [0,-25.66e-37]  # [s^2/m,s^3/m,...]  s^(entry+2)/m
    gamma_test = 0  # 1/W/m
    length_test = 12e3  # m
    number_of_steps = 2**10

    fiber_test = FiberSpan(
        length_test,
        number_of_steps,
        gamma_test,
        beta_list,
        alpha_test,
        use_self_steepening=False,
        describe_fiber_flag=False)

    fiber_list = [fiber_test]  # ,fiber_test_2
    fiber_link = FiberLink(fiber_list)



    test_input_signal = InputSignal(time_freq_test,
                                    test_duration_s,
                                    test_amplitude,
                                    test_pulse_type,
                                    FFT_tol=test_FFT_tol,
                                    describe_input_signal_flag=False)

    theoretical_final_pulse = gaussian_pulse_with_beta_3_only(time_freq_test.t,
                                    test_duration_s,
                                    test_amplitude, beta_list[1],
                                    length_test)

    exp_name = f"unit_test_beta3"
    # Run SSFM
    ssfm_result_list = SSFM(
        fiber_link,
        test_input_signal,
        show_progress_flag=False,
        experiment_name=exp_name,
        FFT_tol=test_FFT_tol
    )
    final_pulse = ssfm_result_list[0].pulse_matrix[-1,:]



    if show_plot_flag:
        fig,ax=plt.subplots(dpi=300)
        #ax.plot(time_freq_test.t/1e-9,get_power(test_input_signal.pulse_field),label = "Initial pulse")
        ax.plot(time_freq_test.t/1e-9,get_power(final_pulse),label = "Final pulse numerical")
        ax.plot(time_freq_test.t/1e-9,get_power(theoretical_final_pulse),label = "Final pulse theoretical")
        ax.set_xlim(-0.5,0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.3),
            ncol=3,
            fancybox=True,
            shadow=True,
        )
        plt.show()

    normalized_energy_diff = compare_field_energies(final_pulse,
                                                    theoretical_final_pulse)
    print(normalized_energy_diff)
    assert normalized_energy_diff<8.0e-6, f"""ERROR: Normalized energy
    difference between numerical and theoretical pulses is
    {normalized_energy_diff =}, but it should be less than or equal to 8.0e-06.
    Unit test for dispersion with beta3 only FAILED!!!"""

    print("Unit test for dispersion with beta3 only SUCCEEDED!")
    print("  ")


def unit_test_nonlinear(show_plot_flag=False):
    unit_test_SPM(show_plot_flag)
    unit_test_self_steepening(show_plot_flag)

def unit_test_SPM(show_plot_flag=False):
    print("  ")
    print("Doing unit test for nonlinear with gamma only!")
    os.chdir(os.path.realpath(os.path.dirname(__file__)))

    N = 2 ** 15  # Number of points
    dt = 100e-15  # Time resolution [s]

    center_freq_test = FREQ_1550_NM_Hz  # FREQ_CENTER_C_BAND_HZ
    time_freq_test = TimeFreq(N,
                              dt,
                              center_freq_test,
                              describe_time_freq_flag=False)

    # Set up signal
    test_FFT_tol = 1e-3
    test_amplitude = 10.0
    test_pulse_type = "gaussian"
    test_amplitude = 0.25
    test_duration_s = 12e-12

    alpha_test = 0  # dB/m
    beta_list = [0]  # [s^2/m,s^3/m,...]  s^(entry+2)/m
    gamma_test = 10e-3  # 1/W/m
    length_test = 12e3  # m
    number_of_steps = 2**10

    fiber_test = FiberSpan(
        length_test,
        number_of_steps,
        gamma_test,
        beta_list,
        alpha_test,
        use_self_steepening=False,
        describe_fiber_flag=False)

    fiber_list = [fiber_test]  # ,fiber_test_2
    fiber_link = FiberLink(fiber_list)



    test_input_signal = InputSignal(time_freq_test,
                                    test_duration_s,
                                    test_amplitude,
                                    test_pulse_type,
                                    FFT_tol=test_FFT_tol,
                                    describe_input_signal_flag=False)


    exp_name = f"unit_test_SPM"
    # Run SSFM
    ssfm_result_list = SSFM(
        fiber_link,
        test_input_signal,
        show_progress_flag=False,
        experiment_name=exp_name,
        FFT_tol=test_FFT_tol
    )
    final_pulse = ssfm_result_list[0].pulse_matrix[-1,:]
    initial_pulse = np.copy(ssfm_result_list[0].pulse_matrix[0,:])
    nonlinear_factor = np.exp(1j*
                              gamma_test*
                              length_test*
                              get_power(initial_pulse))
    theoretical_final_pulse = initial_pulse* nonlinear_factor


    if show_plot_flag:
        fig,ax=plt.subplots(dpi=300)
        ax.plot(time_freq_test.t/1e-9,get_power(final_pulse),label = "Final pulse numerical")
        ax.plot(time_freq_test.t/1e-9,get_power(theoretical_final_pulse),label = "Final pulse theoretical")
        ax.set_xlim(-0.5,0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.3),
            ncol=3,
            fancybox=True,
            shadow=True,
        )
        plt.show()

        fig,ax=plt.subplots(dpi=300)
        ax.plot(time_freq_test.f/1e12,get_power(get_spectrum_from_pulse(time_freq_test.t, final_pulse) ),label = "Final spectrum numerical")
        ax.plot(time_freq_test.f/1e12,get_power(get_spectrum_from_pulse(time_freq_test.t, theoretical_final_pulse)),label = "Final spectrum theoretical")
        ax.set_xlim(-0.5,0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.3),
            ncol=3,
            fancybox=True,
            shadow=True,
        )
        plt.show()


    normalized_energy_diff = compare_field_energies(final_pulse,
                                                    theoretical_final_pulse)

    assert normalized_energy_diff<1.58e-24, f"""ERROR: Normalized energy
    difference between numerical and theoretical pulses is
    {normalized_energy_diff =}, but it should be less than or equal to 7.06e-6.
    Unit test for dispersion with gamma only FAILED!!!"""

    print("Unit test for nonlinearity with gamma only SUCCEEDED!")
    print("  ")

def unit_test_self_steepening(show_plot_flag=False):
    """
    Unit test comparing the theoretical and numerical effects of
    self-steepening with no dispersion or attenuation.

    Parameters
    ----------
    show_plot_flag : Bool, optional
        Flag to toggle shoing graph comparing theoretical to numerical results.
        The default is False.

    Returns
    -------
    None.

    """
    print("  ")
    print("Doing unit test for self steepening only!")
    os.chdir(os.path.realpath(os.path.dirname(__file__)))

    Trange = 0.68e-12
    N = 2 ** 10  # Number of points
    dt = Trange/N  # Time resolution [s]

    centerFreq_test = FREQ_CENTER_C_BAND_HZ*4
    centerWavelength = freq_to_wavelength(centerFreq_test)  # laser wl in m

    time_freq_test = TimeFreq(N,
                              dt,
                              centerFreq_test,
                              describe_time_freq_flag=False)

    beta_list = [0.0]

    fiber_diameter = 9e-6  # m
    n2_silica = 30e-21  # m**2/W

    #
    gamma_test = get_gamma_from_fiber_params(
        centerWavelength, n2_silica, fiber_diameter)

    #  Initialize fibers
    alpha_test = 0

    number_of_steps = 2**9
    testDuration = 0.1e-12/4/1.2171315338170257
    length_test = 8
    spanloss = alpha_test * length_test

    fiber_test = FiberSpan(
        length_test,
        number_of_steps,
        gamma_test,
        beta_list,
        alpha_test,
        use_self_steepening=True,
        describe_fiber_flag=False)

    fiber_list = [fiber_test]
    fiber_link = FiberLink(fiber_list)

    # Set up signal
    test_FFT_tol = 1e-3
    testTimeOffset = 0  # Time offset
    testFreqOffset = 0  # Freq offset from center frequency

    testChirp = 0
    testPulseType = "gauss"
    testOrder = 1
    testNoiseAmplitude = 0

    testAmplitude = 32.320897717179356/2*np.sqrt(1.25)/np.sqrt(2)

    test_input_signal = InputSignal(time_freq_test,
                                    testDuration,
                                    testAmplitude,
                                    testPulseType,
                                    FFT_tol=test_FFT_tol,
                                    describe_input_signal_flag=False)

    print("starting theoretical ss pulse")
    theoretical_final_pulse=self_steepening_pulse(time_freq_test,
                              testDuration,
                              testAmplitude,
                              gamma_test,
                              length_test)

    theoretical_final_pulse=np.abs(theoretical_final_pulse)
    theoretical_final_pulse=np.sqrt(theoretical_final_pulse)
    expName = "unit_test_self_steepening"

    # Run SSFM
    ssfm_result_list = SSFM(
        fiber_link,
        test_input_signal,
        show_progress_flag=False,
        experiment_name=expName,
        FFT_tol=test_FFT_tol
    )
    final_pulse = ssfm_result_list[0].pulse_matrix[-1,:]
    initial_pulse = ssfm_result_list[0].pulse_matrix[0,:]



    if show_plot_flag:
        fig,ax=plt.subplots(dpi=300)
        ax.plot(time_freq_test.t/testDuration,get_power(final_pulse)/testAmplitude**2,label = "Final pulse numerical")
        ax.plot(time_freq_test.t/testDuration,get_power(theoretical_final_pulse),label = "Final pulse theoretical")
        ax.plot(time_freq_test.t/testDuration,get_power(initial_pulse)/testAmplitude**2,alpha=0.4,label = "Initial pulse")
        ax.set_xlim(-3*testDuration/testDuration,3*testDuration/testDuration)
        ax.set_ylim(0,1.02)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.3),
            ncol=3,
            fancybox=True,
            shadow=True,
        )
        plt.show()



    normalized_energy_diff = compare_field_energies(np.abs(final_pulse/testAmplitude),
                                                    theoretical_final_pulse)

    assert normalized_energy_diff<8.12e-07, f"""ERROR: Normalized energy
    difference between numerical and theoretical pulses is
    {normalized_energy_diff =}, but it should be less than or equal to 8.12e-07.
    Unit test for self-steepening only FAILED!!!"""

    print("Unit test for dispersion with self-steepening only SUCCEEDED!")
    print("  ")


if __name__ == "__main__":
    run_all_unit_tests(show_plot_flag=False)
