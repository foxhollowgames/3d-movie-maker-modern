#ifndef PRESENTATIONSDL_H
#define PRESENTATIONSDL_H

#include "presentation.h"

namespace Presentation
{
inline SDL_Texture *CreateFrameTexture(SDL_Renderer *renderer)
{
    uint32_t fabric[TileSize * TileSize];
    for (int y = 0; y < TileSize; ++y)
        for (int x = 0; x < TileSize; ++x)
            fabric[y * TileSize + x] = FramePixel(x, y);
    SDL_Texture *texture =
        SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STATIC, TileSize, TileSize);
    if (texture && SDL_UpdateTexture(texture, nullptr, fabric, TileSize * sizeof(uint32_t)) != 0)
    {
        SDL_DestroyTexture(texture);
        return nullptr;
    }
    return texture;
}

inline void PaintFrame(SDL_Renderer *renderer, SDL_Texture *texture)
{
    int width = 0, height = 0;
    SDL_GetRendererOutputSize(renderer, &width, &height);
    SDL_Rect viewport, clip;
    float scaleX, scaleY;
    Uint8 r, g, b, a;
    SDL_GetRenderDrawColor(renderer, &r, &g, &b, &a);
    SDL_RenderGetScale(renderer, &scaleX, &scaleY);
    SDL_bool clipped = SDL_RenderIsClipEnabled(renderer);
    SDL_RenderGetClipRect(renderer, &clip);
    SDL_RenderSetScale(renderer, 1, 1);
    // Save physical pixels. Logical viewport getters truncate fractional origins.
    SDL_RenderGetViewport(renderer, &viewport);
    SDL_RenderSetViewport(renderer, nullptr);
    SDL_RenderSetClipRect(renderer, nullptr);
    SDL_SetRenderDrawColor(renderer, 23, 19, 32, 255);
    SDL_RenderClear(renderer);
    if (texture)
    {
        Viewport v = {viewport.x, viewport.y, viewport.w, viewport.h};
        for (int y = 0; y < height; y += TileSize)
        {
            for (int x = 0; x < width; x += TileSize)
            {
                if (x >= v.x && y >= v.y && x + TileSize <= v.x + v.width && y + TileSize <= v.y + v.height)
                    continue;
                SDL_Rect tile = {x, y, TileSize, TileSize};
                SDL_RenderCopy(renderer, texture, nullptr, &tile);
            }
        }
        SDL_Rect edge = {v.x - 2, v.y - 2, v.width + 4, v.height + 4};
        SDL_SetRenderDrawColor(renderer, 64, 64, 64, 255);
        SDL_RenderDrawRect(renderer, &edge);
    }
    // Preserve the logical viewport used by SDL's mouse-event conversion.
    SDL_RenderSetViewport(renderer, &viewport);
    SDL_RenderSetScale(renderer, scaleX, scaleY);
    SDL_RenderSetClipRect(renderer, clipped ? &clip : nullptr);
    SDL_SetRenderDrawColor(renderer, r, g, b, a);
}
} // namespace Presentation
#endif
