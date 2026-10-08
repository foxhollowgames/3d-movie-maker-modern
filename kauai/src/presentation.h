// Shared presentation geometry. The authored interface remains 640 by 480.
#ifndef PRESENTATION_H
#define PRESENTATION_H

#include <cstdint>

namespace Presentation
{
constexpr int Width = 640;
constexpr int Height = 480;
constexpr int TileSize = 64;

struct Viewport
{
    int x, y, width, height;
};

inline Viewport Fit(int width, int height)
{
    if (width <= 0 || height <= 0)
        return {0, 0, 0, 0};
    // Whole 4:3 units keep the aspect ratio exact, including odd window sizes.
    int units = width / 4 < height / 3 ? width / 4 : height / 3;
    return {(width - units * 4) / 2, (height - units * 3) / 2, units * 4, units * 3};
}

// Floor division keeps points immediately outside the frame outside the UI.
inline int ToLogical(int value, int origin, int extent, int logicalExtent)
{
    if (extent <= 0)
        return -1;
    int64_t n = int64_t(value - origin) * logicalExtent;
    return int(n >= 0 ? n / extent : -((-n + extent - 1) / extent));
}

inline int ToPhysical(int value, int origin, int extent, int logicalExtent)
{
    return origin + int(int64_t(value) * extent / logicalExtent);
}

// A seamless, subdued purple fabric pattern, generated without external assets.
inline uint32_t FramePixel(int x, int y)
{
    x &= TileSize - 1;
    y &= TileSize - 1;
    int fold = x < 32 ? x : 63 - x;
    int grain = int((uint32_t(x * 37 + y * 101) ^ uint32_t(x * y * 13)) & 7);
    int weave = ((x ^ y) & 1) * 3;
    int r = 23 + fold / 3 + grain + weave;
    int g = 19 + fold / 5 + grain;
    int b = 32 + fold / 2 + grain + weave;
    return 0xff000000u | (uint32_t(r) << 16) | (uint32_t(g) << 8) | uint32_t(b);
}
} // namespace Presentation
#endif
