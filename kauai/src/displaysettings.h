#ifndef DISPLAYSETTINGS_H
#define DISPLAYSETTINGS_H

#include <cstdint>

namespace DisplaySettings
{
struct Size
{
    int width, height;
};

constexpr Size Presets[] = {{0, 0},      {640, 480},  {800, 600},   {1024, 768},  {1280, 720},
                            {1280, 960}, {1600, 900}, {1920, 1080}, {2560, 1440}, {3840, 2160}};
constexpr int PresetCount = sizeof(Presets) / sizeof(Presets[0]);

inline bool ValidSize(int width, int height)
{
    return width >= 320 && height >= 240 && width <= 16384 && height <= 16384;
}

// Sizes are physical client pixels. Keep saved sizes usable after changing monitors.
inline Size FitWindow(int width, int height, int availableWidth, int availableHeight)
{
    if (availableWidth <= 0 || availableHeight <= 0)
        return {1, 1};
    if (!ValidSize(width, height))
        return {availableWidth * 9 / 10 > 0 ? availableWidth * 9 / 10 : 1,
                availableHeight * 9 / 10 > 0 ? availableHeight * 9 / 10 : 1};
    if (width > availableWidth)
    {
        height = int(int64_t(height) * availableWidth / width);
        width = availableWidth;
    }
    if (height > availableHeight)
    {
        width = int(int64_t(width) * availableHeight / height);
        height = availableHeight;
    }
    return {width > 0 ? width : 1, height > 0 ? height : 1};
}
} // namespace DisplaySettings
#endif
