// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// Copyright (C) 2021 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <chrono>
#include <cstdint>
#include <ctime>
#include <memory>
#include <string>

namespace pisa {
namespace common {

/**
 * @brief SimpleTimer
 * @details
 * This class provides operations to track time.
 *
 * This timer is as precise as EventTimer. Difference between these classes
 * is in the features and flexibility offered.
 *
 * To measure execution time of a portion of code, sandwich the code between
 * calls to `start()` and `stop()`.
 */
class SimpleTimer
{
public:
    /**
     * @brief Constructor for the SimpleTimer Class
     * @param high_precision - flag to use high precision for time
     * @param start_active   - flag to start timer instantly
     */
    SimpleTimer(bool high_precision = false, bool start_active = false)
    {
        m_active              = false;
        m_high_precision_mode = high_precision;
        if (start_active == true)
        {
            start();
        }
    }

    /**
     * @brief start timer instantly
     */
    void start()
    {
        if (m_high_precision_mode)
            m_high_start_time = std::chrono::high_resolution_clock::now();
        else
            m_start_time = std::chrono::system_clock::now();

        m_active = true;
    }

    /**
     * @brief Stop timer instanstly
     * @details Use `elapsedSeconds()`, `elapsedMilliseconds()` and `elapsedMicroseconds()`
     * methods to retrieve the time elapsed between the last call to `start()` and
     * this call.
     */
    void stop()
    {
        if (m_high_precision_mode)
            m_high_end_time = std::chrono::high_resolution_clock::now();
        else
            m_end_time = std::chrono::system_clock::now();

        m_active = false;
    }

    /**
     * @brief indicate the timer is active or not
     * @return boolean - status of the timer
     */
    bool isActive() { return m_active; }

    /**
     * @brief number of ellapse time that timer is holding
     * @param micro - indicates returning in ms or micro-second
     * @return number of elappsed millli-second or micro-second
     */
    double elapsedMilliseconds(bool micro = false)
    {
        std::chrono::time_point<std::chrono::system_clock> endTime;
        std::chrono::time_point<std::chrono::high_resolution_clock> highEndTime;

        if (m_active)
        {
            if (m_high_precision_mode)
                highEndTime = std::chrono::high_resolution_clock::now();
            else
                endTime = std::chrono::system_clock::now();
        }
        else
        {
            if (m_high_precision_mode)
                highEndTime = m_high_end_time;
            else
                endTime = m_end_time;
        }

        if (micro == false)
        {
            if (m_high_precision_mode)
                return std::chrono::duration<double, std::milli>(highEndTime - m_high_start_time).count();
            else
                return std::chrono::duration<double, std::milli>(endTime - m_start_time).count();
        }
        else
        {
            if (m_high_precision_mode)
                return std::chrono::duration<double, std::micro>(highEndTime - m_high_start_time).count();
            else
                return std::chrono::duration<double, std::micro>(endTime - m_start_time).count();
        }
    }

    /**
     * @brief number of elapse time that timer is holding
     * @return number of elapsed second
     */
    double elapsedSeconds() { return elapsedMilliseconds() / 1000.0; }

    /**
     * @brief number of elapse time that timer is holding
     * @return number of elappsed micro second
     */
    double elapsedMicroSeconds() { return elapsedMilliseconds(true); }

private:
    // Standard
    std::chrono::time_point<std::chrono::system_clock> m_start_time;
    std::chrono::time_point<std::chrono::system_clock> m_end_time;

    // High
    std::chrono::time_point<std::chrono::high_resolution_clock> m_high_start_time;
    std::chrono::time_point<std::chrono::high_resolution_clock> m_high_end_time;

    bool m_active;
    bool m_high_precision_mode;
};

/**
 * @brief Type of objects returned by an EventTimer.
 * @details Methods of this class are templated to allow transparent
 * conversion to different time scales based on the time interval
 * template argument specified as a std::ratio.
 */
class TimingReportEvent
{
public:
    template <bool>
    friend class EventTimer;

    /**
     * Default time interval used for all interval-templated operations.
     * Defaults to seconds.
     */
    using DefaultTimeInterval = std::ratio<1, 1>; // all times in seconds by default: report will convert to other units if needed

    // set a timing to 0 to ignore in reports

    /**
     * @brief Construct a new TimingReportEvent object.
     * @param[in] _id Optional ID to associate with this event.
     * @param[in] _description Optional text description to add to this event.
     */
    TimingReportEvent(std::uint32_t _id = 0, const std::string &_description = std::string()) :
        id(_id),
        description(_description),
        m_cpu_time_start(0.0),
        m_cpu_time_end(0.0),
        m_wall_time_start(0.0),
        m_wall_time_end(0.0),
        m_iterations(1),
        m_ratio_numerator(1),
        m_ratio_denominator(1)
    {
    }

    typedef std::shared_ptr<TimingReportEvent> Ptr;
    /**
     * @brief Construct a new smart pointer to a TimingReportEvent object.
     * @param[in] id Optional ID to associate with this event.
     * @param[in] description Optional text description to add to this event.
     */
    static TimingReportEvent::Ptr create(std::uint32_t id = 0, const std::string &description = std::string())
    {
        return TimingReportEvent::Ptr(new TimingReportEvent(id, description));
    }

    /**
     * @brief ID of this event.
     */
    std::uint32_t id;
    /**
     * @brief Description of this event.
     */
    std::string description;

    template <class TimeInterval = DefaultTimeInterval> // TimeInterval = std::nano, std::micro, std::milli, std::ratio<1, 1>, etc.
    /**
     * @brief Retrieves the absolute CPU timing at which this event started.
     * @return System dependent absolute CPU timing at which this event started.
     * @details This value is generally meaningless on its own. The total CPU
     * time for this event is actually computed as the difference between
     * timeEndCPU() and timeStartCPU() in the same TimeInterval i.e.
     *
     * @code
     * double elapsed_time = timeEndCPU() - timeStartCPU();
     * @endcode
     * @sa elapsedCPUTime()
     */
    double timeStartCPU() const
    {
        return m_cpu_time_start * convertTimeInterval<TimeInterval>();
    }
    template <class TimeInterval = DefaultTimeInterval> // TimeInterval = std::nano, std::micro, std::milli, std::ratio<1, 1>, etc.
    /**
     * @brief Retrieves the absolute CPU timing at which this event ended.
     * @return System dependent absolute CPU timing at which this event ended.
     * @details This value is generally meaningless on its own. The total CPU
     * time for this event is actually computed as the difference between
     * timeEndCPU() and timeStartCPU() in the same TimeInterval i.e.
     *
     * @code
     * double elapsed_time = timeEndCPU() - timeStartCPU();
     * @endcode
     * @sa elapsedCPUTime()
     */
    double timeEndCPU() const
    {
        return m_cpu_time_end * convertTimeInterval<TimeInterval>();
    }
    template <class TimeInterval = DefaultTimeInterval> // TimeInterval = std::nano, std::micro, std::milli, std::ratio<1, 1>, etc.
    /**
     * @brief Retrieves the absolute wall timing at which this event started.
     * @return System dependent absolute wall timing at which this event started.
     * @details This value is generally meaningless on its own. The total wall
     * time for this event is actually computed as the difference between
     * timeEndWall() and timeStartWall() in the same TimeInterval i.e.
     *
     * @code
     * double elapsed_time = timeEndWall() - timeStartWall();
     * @endcode
     * @sa elapsedWallTime()
     */
    double timeStartWall() const
    {
        return m_wall_time_start * convertTimeInterval<TimeInterval>();
    }
    template <class TimeInterval = DefaultTimeInterval> // TimeInterval = std::nano, std::micro, std::milli, std::ratio<1, 1>, etc.
    /**
     * @brief Retrieves the absolute wall timing at which this event ended.
     * @return System dependent absolute wall timing at which this event ended.
     * @details This value is generally meaningless on its own. The total wall
     * time for this event is actually computed as the difference between
     * timeEndWall() and timeStartWall() in the same TimeInterval i.e.
     *
     * @code
     * double elapsed_time = timeEndWall() - timeStartWall();
     * @endcode
     * @sa elapsedWallTime()
     */
    double timeEndWall() const
    {
        return m_wall_time_end * convertTimeInterval<TimeInterval>();
    }

    /**
     * @brief Number of iterations that occurred in this event.
     * @details This value is for information purposes only and can be used
     * to express a bulk of events that may be bundled in this event report.
     */
    std::uint64_t iterations() const { return m_iterations; }

    template <class TimeInterval = DefaultTimeInterval> // TimeInterval = std::nano, std::micro, std::milli, std::ratio<1, 1>, etc.
    /**
     * @brief Retrieves the elapsed CPU time for this event.
     * @return The elapsed CPU time for this event in the specified TimeInterval scale.
     * @details If no threads are idle (waiting on mutexes or sleeping) during the event
     * timed, the following is true:
     *
     * @code
     * elapsedCPUTime() = elapsedWallTime() * number_of_threads
     * @endcode
     *
     * The above is in ideal conditions, but in practice, this is an approximation.
     *
     * The following indicates idle threads or high levels of contention among threads:
     *
     * @code
     * elapsedCPUTime() < < elapsedWallTime() * number_of_threads
     * @endcode
     */
    double elapsedCPUTime() const
    {
        return (m_cpu_time_end - m_cpu_time_start) * convertTimeInterval<TimeInterval>();
    }
    template <class TimeInterval = DefaultTimeInterval> // TimeInterval = std::nano, std::micro, std::milli, std::ratio<1, 1>, etc.
    /**
     * @brief Retrieves the elapsed wall time for this event.
     * @return The elapsed wall time for this event in the specified TimeInterval scale.
     */
    double elapsedWallTime() const
    {
        return (m_wall_time_end - m_wall_time_start) * convertTimeInterval<TimeInterval>();
    }

protected:
    template <class TimeInterval = DefaultTimeInterval> // TimeInterval = std::nano, std::micro, std::milli, std::ratio<1, 1>, etc.
    /**
     * @brief Sets the timing values for this timing event.
     * @param[in] cpu_time_start CPU start time in the specified time interval unit.
     * @param[in] cpu_time_end CPU end time in the specified time interval unit.
     * @param[in] wall_time_start Wall start time in the specified time interval unit.
     * @param[in] wall_time_end Wall end time in the specified time interval unit.
     * @param[in] iterations Number of iterations contained this event.
     */
    void setTimings(double cpu_time_start, double cpu_time_end,
                    double wall_time_start, double wall_time_end,
                    std::uint64_t iterations)
    {
        m_ratio_numerator   = TimeInterval::num;
        m_ratio_denominator = TimeInterval::den;
        m_cpu_time_start    = (cpu_time_start > cpu_time_end ? cpu_time_end : cpu_time_start);
        m_cpu_time_end      = (cpu_time_start > cpu_time_end ? cpu_time_start : cpu_time_end);
        m_wall_time_start   = (wall_time_start > wall_time_end ? wall_time_end : wall_time_start);
        m_wall_time_end     = (wall_time_start > wall_time_end ? wall_time_start : wall_time_end);
        m_iterations        = iterations;
    }

private:
    template <class TimeInterval>
    double convertTimeInterval() const
    {
        return (static_cast<double>(m_ratio_numerator) * TimeInterval::den) / (m_ratio_denominator * TimeInterval::num);
    }

    double m_cpu_time_start;
    double m_cpu_time_end;
    double m_wall_time_start;
    double m_wall_time_end;
    std::uint64_t m_iterations;
    std::intmax_t m_ratio_numerator;
    std::intmax_t m_ratio_denominator;
};

template <bool high_precision = false>
/**
 * @brief Timer class that allows advanced time tracking of events and
 * time interval manipulation.
 *
 * If template parameter `high_precision` is true, then this timer will
 * attempt to use the highest precision clock available in the system
 * to measure wall time, otherwise, the system clock will be used.
 *
 * This timer is as precise as SimpleTimer. Difference between these classes
 * is in the features and flexibility offered. If only basic timing is
 * needed, SimpleTimer will offer a quick solution. If extra features
 * such as CPU time, flexible time scales, then, this class is better.
 *
 * To measure execution time of a portion of code, sandwich the code between
 * calls to `start()` and `stop()`.
 */
class EventTimer
{
public:
    /**
     * @brief Constructs a new EventTimer object.
     * @param[in] start_active If `true`, the timer is constructed and started.
     * Otherwise, the timer is idle and waiting to be started.
     */
    EventTimer(bool start_active = false)
    {
        m_active         = false;
        m_cpu_start_time = std::clock();
        m_start_time     = ClockType::now();
        // compute the 0 time
        m_cpu_init_time = std::clock();
        m_init_time     = ClockType::now();

        if (start_active)
            start();
    }

    /**
     * @brief Starts measuring time from this call and until stopped.
     */
    void start()
    {
        m_active         = true;
        m_cpu_start_time = std::clock();
        m_start_time     = ClockType::now();
    }

    template <class TimeInterval = TimingReportEvent::DefaultTimeInterval> // TimeInterval = std::nano, std::micro, std::milli, std::ratio<1, 1>, etc.
    /**
     * @brief Stops measuring time.
     * @param[in] iterations Number of iterations measured in this event.
     * @return A TimingReportEvent with the measurement details.
     * @details
     * The returned event report will reflect the timings between the latest call
     * to `start()` and this call.
     * @sa TimingReportEvent::iterations()
     */
    TimingReportEvent::Ptr stop(std::uint64_t iterations = 1)
    {
        return stop<TimeInterval>(0, iterations, nullptr);
    }
    template <class TimeInterval = TimingReportEvent::DefaultTimeInterval> // TimeInterval = std::nano, std::micro, std::milli, std::ratio<1, 1>, etc.
    /**
     * @brief Stops measuring time.
     * @param[in] id Optional ID to associate with this event.
     * @param[in] iterations Number of iterations measured in this event.
     * @param[in] description Optional text description to add to this event.
     * @return A TimingReportEvent with the measurement details.
     * @details
     * The returned event report will reflect the timings between the latest call
     * to `start()` and this call.
     * @sa TimingReportEvent::iterations()
     */
    TimingReportEvent::Ptr stop(std::uint32_t id,
                                std::uint64_t iterations,
                                const char *description)
    {
        double cpu_end_time  = getCPUElapsedTime<TimeInterval>();
        double wall_end_time = getWallElapsedTime<TimeInterval>();
        m_active             = false;

        TimingReportEvent::Ptr retval = TimingReportEvent::create(id,
                                                                  description ? std::string(description) : std::string());
        retval->setTimings<TimeInterval>(
            getCPUElapsedTime<TimeInterval>(m_cpu_start_time), cpu_end_time,
            getWallElapsedTime<TimeInterval>(m_start_time), wall_end_time,
            iterations);

        return retval;
    }

    /**
     * @brief Retrieves whether the timer is active.
     * @returns `true` if a call to `start()` has been made without a matching call
     * to `stop()`, i.e. the timer is active.
     * @returns `false` otherwise.
     */
    bool isActive() const { return m_active; }

private:
    typedef typename std::conditional<high_precision,
                                      std::chrono::high_resolution_clock,
                                      std::chrono::system_clock>::type ClockType;

    template <class TimeInterval>
    double getCPUElapsedTime() const
    {
        return getCPUElapsedTime<TimeInterval>(std::clock());
    }
    template <class TimeInterval>
    double getCPUElapsedTime(std::clock_t cpu_end_time) const
    {
        return (cpu_end_time - m_cpu_init_time) * static_cast<double>(TimeInterval::den) / (static_cast<double>(CLOCKS_PER_SEC) * static_cast<double>(TimeInterval::num));
    }
    template <class TimeInterval>
    double getWallElapsedTime() const
    {
        return getWallElapsedTime<TimeInterval>(ClockType::now());
    }
    template <class TimeInterval>
    double getWallElapsedTime(const std::chrono::time_point<ClockType> &end_time) const
    {
        return std::chrono::duration<double, TimeInterval>(end_time - m_init_time).count();
    }

    std::chrono::time_point<ClockType> m_init_time;
    std::clock_t m_cpu_init_time;
    std::chrono::time_point<ClockType> m_start_time;
    std::clock_t m_cpu_start_time;

    bool m_active;
};

} // namespace common
} // namespace pisa
