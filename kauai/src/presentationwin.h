#ifndef PRESENTATIONWIN_H
#define PRESENTATIONWIN_H

#include "presentation.h"

namespace Presentation
{
// Opt in only for the movie application. Kauai's other tools keep native sizing.
inline HWND window = nullptr;

inline bool Active(HWND hwnd)
{
    return window != nullptr && hwnd == window;
}

inline Viewport WindowViewport()
{
    RECT rc = {};
    GetClientRect(window, &rc);
    return Fit(rc.right, rc.bottom);
}

inline void ClientToLogical(HWND hwnd, POINT *pt)
{
    if (!Active(hwnd))
        return;
    auto v = WindowViewport();
    pt->x = ToLogical(pt->x, v.x, v.width, Width);
    pt->y = ToLogical(pt->y, v.y, v.height, Height);
}

inline void LogicalToClient(HWND hwnd, POINT *pt)
{
    if (!Active(hwnd))
        return;
    auto v = WindowViewport();
    pt->x = ToPhysical(pt->x, v.x, v.width, Width);
    pt->y = ToPhysical(pt->y, v.y, v.height, Height);
}

inline RECT PhysicalRect(HWND hwnd, RECT rc)
{
    if (!Active(hwnd))
        return rc;
    auto v = WindowViewport();
    // Round outward so invalidation never loses an edge pixel.
    rc.left = v.x + rc.left * v.width / Width;
    rc.top = v.y + rc.top * v.height / Height;
    rc.right = v.x + (rc.right * v.width + Width - 1) / Width;
    rc.bottom = v.y + (rc.bottom * v.height + Height - 1) / Height;
    return rc;
}

inline void LogicalUpdateRect(HWND hwnd, RECT *rc)
{
    GetUpdateRect(hwnd, rc, FALSE);
    if (Active(hwnd) && !IsRectEmpty(rc))
        SetRect(rc, 0, 0, Width, Height);
}

inline void PaintFrame(HDC dc, const RECT &client, const Viewport &v)
{
    struct FabricBrush
    {
        HBRUSH brush = nullptr;
        FabricBrush()
        {
            BITMAPINFO info = {};
            info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
            info.bmiHeader.biWidth = TileSize;
            info.bmiHeader.biHeight = -TileSize;
            info.bmiHeader.biPlanes = 1;
            info.bmiHeader.biBitCount = 32;
            void *pixels = nullptr;
            HBITMAP bitmap = CreateDIBSection(nullptr, &info, DIB_RGB_COLORS, &pixels, nullptr, 0);
            if (bitmap)
            {
                for (int y = 0; y < TileSize; ++y)
                    for (int x = 0; x < TileSize; ++x)
                        static_cast<uint32_t *>(pixels)[y * TileSize + x] = FramePixel(x, y);
                brush = CreatePatternBrush(bitmap);
                DeleteObject(bitmap);
            }
        }
        ~FabricBrush()
        {
            if (brush)
                DeleteObject(brush);
        }
    };
    static FabricBrush fabric;
    int saved = SaveDC(dc);
    if (!saved)
        return;
    ExcludeClipRect(dc, v.x, v.y, v.x + v.width, v.y + v.height);
    FillRect(dc, &client, fabric.brush ? fabric.brush : (HBRUSH)GetStockObject(BLACK_BRUSH));
    RECT edge = {v.x - 3, v.y - 3, v.x + v.width + 3, v.y + v.height + 3};
    FrameRect(dc, &edge, (HBRUSH)GetStockObject(DKGRAY_BRUSH));
    InflateRect(&edge, -1, -1);
    FrameRect(dc, &edge, (HBRUSH)GetStockObject(BLACK_BRUSH));
    RestoreDC(dc, saved);
}
} // namespace Presentation
#endif
