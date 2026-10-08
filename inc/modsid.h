// Copyright (c) Fox Hollow Games. Licensed under the MIT License.
#ifndef MODSID_H
#define MODSID_H

#include <cstdint>

// The directory is the source name saved in movies. Keep it stable when sharing.
// Canonical decimal names prevent two directories from claiming the same ID.
template <class Char> int32_t ModSourceId(const Char *name)
{
    const char *prefix = "FHMod";
    while (*prefix)
    {
        if (*name++ != *prefix++)
            return 0;
    }
    if (*name < '1' || *name > '9')
        return 0;
    int32_t value = 0;
    while (*name)
    {
        if (*name < '0' || *name > '9')
            return 0;
        const int32_t digit = *name++ - '0';
        if (value > (INT32_MAX - 1 - digit) / 10)
            return 0;
        value = value * 10 + digit;
    }
    return value >= 1000 ? value : 0;
}

#endif
