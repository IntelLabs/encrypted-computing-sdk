// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace pisa {

template <typename T>
class MultiRegister
{
public:
    MultiRegister() = default;
    MultiRegister(std::size_t size_in_elements) :
        m_data(size_in_elements)
    {
    }

    MultiRegister(std::size_t size_in_elements, const T &value) :
        m_data(size_in_elements, value)
    {
    }

    MultiRegister(const std::vector<T> &data) :
        m_data(data)
    {
    }

    std::string toString();
    void toCSV(std::ostream &output_stream)
    {
        for (auto x : m_data)
        {
            output_stream << "," << x;
        }
    }

    MultiRegister<T> operator+(const MultiRegister<T> &src1);

    MultiRegister operator-(const MultiRegister &src1)
    {
        try
        {
            if (src1.m_data.size() != m_data.size())
            {
                throw std::runtime_error("Error adding MultiRegisters, sizes are not equal");
            }
            MultiRegister output(m_data.size());
#pragma omp parallel for
            for (size_t x = 0; x < output.m_data.size(); x++)
            {
                output.m_data[x] = m_data[x] - src1.m_data[x];
            }
            return output;
        }
        catch (...)
        {
            throw;
        }
    }

    MultiRegister montgomeryAddModulus(u_int64_t modulus)
    {
        try
        {
            MultiRegister output(m_data.size());

            output.m_data = m_data;
#pragma omp parallel for
            for (auto &u : output.m_data)
            {
                if (u >= 2 * modulus)
                    throw std::runtime_error("Value out of bounds");

                // branchless if
                u = u - (u >= modulus) * modulus;
            }

            return output;
        }
        catch (const std::runtime_error &err)
        {
            std::cout << "Runtime Error in montgomeryAdd: " << err.what() << std::endl;
            throw err;
        }
        catch (...)
        {
            throw;
        }
    }

    MultiRegister operator*(const MultiRegister &src1) const
    {
        try
        {
            if (src1.m_data.size() != m_data.size())
            {
                throw std::runtime_error("Error adding MultiRegisters, Sizes are not equal");
            }

            MultiRegister output(m_data.size());
#pragma omp parallel for
            for (size_t x = 0; x < output.m_data.size(); x++)
            {
                output.m_data[x] = m_data[x] * src1.m_data[x];
            }
            return output;
        }
        catch (...)
        {
            throw;
        }
    }

    MultiRegister operator*(const T &src1) const
    {
        try
        {
            MultiRegister output(m_data.size());
#pragma omp parallel for
            for (size_t x = 0; x < output.m_data.size(); x++)
            {
                output.m_data[x] = m_data[x] * src1;
            }
            return output;
        }
        catch (...)
        {
            throw;
        }
    }

    MultiRegister montgomeryMulModulus(uint64_t modulus)
    {
        MultiRegister output(m_data.size());

        output.m_data = m_data;
#pragma omp parallel for
        for (auto &u : output.m_data)
        {
            uint64_t k = modulus - 2;
            uint64_t t = u & std::numeric_limits<uint>::max();
            uint64_t m = (t * k) & std::numeric_limits<uint>::max();
            u += m * modulus;
            u >>= 32;
            // branchless if
            u = u - (u >= modulus) * modulus;
        }

        return output;
    }

    MultiRegister operator%(const T &src1) const
    {
        try
        {
            MultiRegister output(m_data.size());
#pragma omp parallel for
            for (size_t x = 0; x < output.m_data.size(); x++)
            {
                output.m_data[x] = m_data[x] % src1;
            }
            return output;
        }
        catch (...)
        {
            throw;
        }
    }

    MultiRegister rotate(int num)
    {
        MultiRegister output(m_data.size());
#pragma omp parallel for
        for (int x = 0; x < m_data.size(); x++)
        {
            output.m_data[x] = m_data[(x + num) % m_data.size()];
        }
        return output;
    }

    void resize(int val)
    {
        m_data.resize(val);
    }

    int size()
    {
        return m_data.size();
    }

    std::vector<T> &data()
    {
        return m_data;
    }

    void setData(const std::vector<T> &newData)
    {
        m_data = newData;
    }

    T &operator[](size_t index)
    {
        return m_data[index];
    }

private:
    std::vector<T> m_data;
};

template <typename T>
std::string MultiRegister<T>::toString()
{
    char comma[] = { '\0', '\0' };
    std::ostringstream str_vec;
    str_vec << '[';
    for (const auto &datum : m_data)
    {
        str_vec << comma << datum;
        comma[0] = ',';
    }
    str_vec << ']';
    return str_vec.str();
}

template <typename T>
MultiRegister<T> MultiRegister<T>::operator+(const MultiRegister<T> &src1)
{
    try
    {
        if (src1.m_data.size() != m_data.size())
        {
            throw std::runtime_error("Error adding MultiRegisters, Sizes are not equal");
        }
        MultiRegister output(m_data.size());
#pragma omp parallel for
        for (size_t x = 0; x < output.m_data.size(); x++)
        {
            output.m_data[x] = m_data[x] + src1.m_data[x];
        }
        return output;
    }
    catch (...)
    {
        throw;
    }
}

} // namespace pisa
