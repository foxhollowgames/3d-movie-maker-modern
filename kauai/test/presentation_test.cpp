#include "presentation.h"
#include "displaysettings.h"
#include <cstdio>
#include <cstdlib>

#ifdef PRESENTATION_TEST_SDL
#define SDL_MAIN_HANDLED
#include <SDL.h>
#include "presentationsdl.h"
#endif

#ifdef _WIN32
#include <windows.h>
#include "presentationwin.h"
#endif

static void Check(bool passed, const char *message)
{
    if (!passed)
    {
        std::fprintf(stderr, "Presentation test failed: %s\n", message);
        std::exit(1);
    }
}

int main()
{
    using namespace Presentation;
    auto automatic = DisplaySettings::FitWindow(0, 0, 1904, 1033);
    Check(automatic.width == 1713 && automatic.height == 929, "automatic window follows usable display size");
    auto configured = DisplaySettings::FitWindow(1280, 720, 1904, 1033);
    Check(configured.width == 1280 && configured.height == 720, "configured resolution is retained when it fits");
    auto smallerMonitor = DisplaySettings::FitWindow(3840, 2160, 1264, 673);
    Check(smallerMonitor.width <= 1264 && smallerMonitor.height <= 673, "saved resolution fits a smaller monitor");
    auto invalid = DisplaySettings::FitWindow(-1, 999999, 1904, 1033);
    Check(invalid.width == automatic.width && invalid.height == automatic.height,
          "invalid settings fall back to automatic");
    auto portrait = DisplaySettings::FitWindow(1920, 1080, 704, 1233);
    Check(portrait.width == 704 && portrait.height == 396, "saved size adapts to portrait displays");
    Check(DisplaySettings::FitWindow(0, 0, 0, 0).width == 1, "unavailable display has a safe fallback");
    const int sizes[][2] = {{640, 480},   {1280, 720},  {1920, 1080}, {2560, 1440}, {3840, 2160},
                            {3440, 1440}, {5120, 1440}, {1080, 1920}, {1365, 767},  {320, 240}};
    for (const auto &size : sizes)
    {
        auto v = Fit(size[0], size[1]);
        Check(v.width * 3 == v.height * 4, "4:3 proportions");
        Check(v.x >= 0 && v.y >= 0 && v.x + v.width <= size[0] && v.y + v.height <= size[1], "no cropping");
        Check(size[0] - v.width - 2 * v.x <= 1 && size[1] - v.height - 2 * v.y <= 1, "centered content");
        Check(ToLogical(v.x - 1, v.x, v.width, Width) < 0, "left frame does not activate controls");
        Check(ToLogical(v.y - 1, v.y, v.height, Height) < 0, "top frame does not activate controls");
        Check(ToLogical(v.x + v.width, v.x, v.width, Width) == Width, "right frame is outside content");
        Check(ToLogical(v.y + v.height, v.y, v.height, Height) == Height, "bottom frame is outside content");
        Check(ToLogical(v.x + v.width - 1, v.x, v.width, Width) < Width, "last content pixel is inside");
        for (int x = 0; x < v.width; ++x)
        {
            int logical = ToLogical(v.x + x, v.x, v.width, Width);
            Check(logical >= 0 && logical < Width, "every horizontal pixel maps to a valid control coordinate");
        }
        Check(ToLogical(v.x + v.width / 2, v.x, v.width, Width) == 320, "horizontal center maps to 320");
        int centerY = ToLogical(v.y + v.height / 2, v.y, v.height, Height);
        Check(centerY >= 239 && centerY <= 240, "vertical center accounts for odd pixel heights");
    }
    auto hd = Fit(1920, 1080);
    Check(hd.x == 240 && hd.y == 0 && hd.width == 1440 && hd.height == 1080, "1080p viewport");
    auto ultra = Fit(3440, 1440);
    Check(ultra.x == 760 && ultra.width == 1920, "ultrawide viewport");
    Check(Fit(0, 0).width == 0 && Fit(1920, 0).height == 0, "minimized window");
    Check(ToLogical(0, 0, 0, Width) == -1, "empty viewport has no hit target");
    for (int y = 0; y < TileSize; ++y)
        for (int x = 0; x < TileSize; ++x)
            Check(FramePixel(x, y) == FramePixel(x + TileSize, y + TileSize), "texture repeats without missing tiles");

#ifdef _WIN32
    HWND hwnd = CreateWindowA("STATIC", "Presentation tests", WS_POPUP, 0, 0, 1920, 1080, nullptr, nullptr,
                              GetModuleHandle(nullptr), nullptr);
    Check(hwnd != nullptr, "create hidden test window");
    window = hwnd;
    POINT point = {240, 0};
    ClientToLogical(hwnd, &point);
    Check(point.x == 0 && point.y == 0, "native hit testing uses the content origin");
    point = {320, 240};
    LogicalToClient(hwnd, &point);
    Check(point.x == 960 && point.y == 540, "native cursor placement uses scaled coordinates");
    RECT dirty = PhysicalRect(hwnd, {0, 0, 1, 1});
    Check(dirty.left == 240 && dirty.top == 0 && dirty.right == 243 && dirty.bottom == 3,
          "invalidation rounds fractional pixels outward");
    HDC dc = CreateCompatibleDC(nullptr);
    BITMAPINFO info = {};
    info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    info.bmiHeader.biWidth = 1920;
    info.bmiHeader.biHeight = -1080;
    info.bmiHeader.biPlanes = 1;
    info.bmiHeader.biBitCount = 32;
    void *pixels = nullptr;
    HBITMAP bitmap = CreateDIBSection(dc, &info, DIB_RGB_COLORS, &pixels, nullptr, 0);
    Check(dc && bitmap, "allocate native frame render target");
    HGDIOBJ previous = SelectObject(dc, bitmap);
    RECT client = {0, 0, 1920, 1080};
    FillRect(dc, &client, (HBRUSH)GetStockObject(WHITE_BRUSH));
    PaintFrame(dc, client, hd);
    GdiFlush();
    Check(GetPixel(dc, 0, 0) != RGB(255, 255, 255), "frame fills unused space");
    Check(GetPixel(dc, 960, 540) == RGB(255, 255, 255), "frame never covers the content");
    Check(GetPixel(dc, 0, 0) != GetPixel(dc, 17, 9), "frame contains texture");
    SelectObject(dc, previous);
    DeleteObject(bitmap);
    DeleteDC(dc);
    window = nullptr;
    DestroyWindow(hwnd);
#endif

#ifdef PRESENTATION_TEST_SDL
    SDL_SetMainReady();
    Check(SDL_Init(SDL_INIT_VIDEO) == 0, "initialize SDL video");
    SDL_Window *sdlWindow = SDL_CreateWindow("Presentation test", 0, 0, 1280, 720, SDL_WINDOW_HIDDEN);
    Check(sdlWindow != nullptr, "create hidden SDL test window");
    SDL_Renderer *renderer = SDL_CreateRenderer(sdlWindow, -1, SDL_RENDERER_SOFTWARE);
    Check(renderer != nullptr, "create SDL software renderer");
    Check(SDL_RenderSetLogicalSize(renderer, Width, Height) == 0, "set authored SDL layout");
    SDL_Texture *fabric = CreateFrameTexture(renderer);
    Check(fabric != nullptr, "create SDL fabric texture");
    SDL_Rect clip = {20, 20, 600, 440};
    SDL_RenderSetClipRect(renderer, &clip);
    const int renderSizes[][2] = {{1280, 720}, {1365, 767}, {960, 1080}};
    for (int frame = 0; frame < 3; ++frame)
    {
        int renderWidth = renderSizes[frame][0], renderHeight = renderSizes[frame][1];
        SDL_SetWindowSize(sdlWindow, renderWidth, renderHeight);
        SDL_PumpEvents();
        SDL_RenderSetLogicalSize(renderer, Width, Height);
        SDL_RenderSetClipRect(renderer, &clip);
        SDL_Rect before, after, clipAfter;
        float mouseXBefore, mouseYBefore, mouseXAfter, mouseYAfter;
        SDL_RenderGetViewport(renderer, &before);
        SDL_RenderWindowToLogical(renderer, renderWidth / 2, renderHeight / 2, &mouseXBefore, &mouseYBefore);
        PaintFrame(renderer, fabric);
        SDL_RenderGetViewport(renderer, &after);
        SDL_RenderWindowToLogical(renderer, renderWidth / 2, renderHeight / 2, &mouseXAfter, &mouseYAfter);
        SDL_RenderGetClipRect(renderer, &clipAfter);
        Check(before.x == after.x && before.y == after.y && before.w == after.w && before.h == after.h,
              "SDL viewport survives frame painting");
        Check(mouseXBefore == mouseXAfter && mouseYBefore == mouseYAfter,
              "SDL mouse transform survives frame painting");
        Check(SDL_RenderIsClipEnabled(renderer) && clipAfter.x == clip.x && clipAfter.y == clip.y &&
                  clipAfter.w == clip.w && clipAfter.h == clip.h,
              "SDL clipping survives frame painting");
        SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255);
        SDL_RenderFillRect(renderer, nullptr);
        // Read a physical pixel in the content center, then one in the left frame.
        SDL_RenderSetClipRect(renderer, nullptr);
        SDL_RenderSetLogicalSize(renderer, 0, 0);
        SDL_Rect sample = {renderWidth / 2, renderHeight / 2, 1, 1};
        uint32_t pixel = 0;
        Check(SDL_RenderReadPixels(renderer, &sample, SDL_PIXELFORMAT_ARGB8888, &pixel, 4) == 0,
              "read SDL rendered content");
        Check((pixel & 0xffffff) == 0xff0000, "SDL content stays centered");
        if (renderWidth * 3 > renderHeight * 4)
            sample.x = 0;
        else
            sample.y = 0;
        Check(SDL_RenderReadPixels(renderer, &sample, SDL_PIXELFORMAT_ARGB8888, &pixel, 4) == 0,
              "read SDL rendered frame");
        Check((pixel & 0xffffff) != 0xff0000 && (pixel & 0xffffff) != 0, "SDL frame contains fabric");
        SDL_RenderSetLogicalSize(renderer, Width, Height);
        SDL_RenderSetClipRect(renderer, &clip);
        SDL_RenderPresent(renderer);
    }
    SDL_DestroyTexture(fabric);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(sdlWindow);
    SDL_Quit();
    std::puts("SDL frame painting, clipping, and mouse transforms passed.");
#endif
    std::puts("Presentation tests passed: 10 screen sizes, input boundaries, minimization, texture, and native frame "
              "painting.");
    return 0;
}
