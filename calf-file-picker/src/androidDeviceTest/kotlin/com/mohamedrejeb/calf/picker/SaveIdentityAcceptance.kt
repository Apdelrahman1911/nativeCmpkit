package com.mohamedrejeb.calf.picker

/**
 * Exact native saver acceptance group. A single annotation selector survives
 * AGP's Android Test Engine argument transport without a comma-separated value.
 * The CI controller independently requires every selected testcase in fresh XML.
 */
@Target(AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
annotation class SaveIdentityAcceptance

/** The independently accepted descriptor calibration, reusable by focused recovery. */
@Target(AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
annotation class SaveIdentityCalibration
