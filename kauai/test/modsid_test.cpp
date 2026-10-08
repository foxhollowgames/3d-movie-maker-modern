#include "../../inc/modsid.h"
#include <gtest/gtest.h>
#include "util.h"
#include "resources.h"

ASSERTNAME

TEST(ModSource, CanonicalNames)
{
    EXPECT_EQ(ModSourceId("FHMod1000"), 1000);
    EXPECT_EQ(ModSourceId(L"FHMod2147483646"), 2147483646);
    for (const char *name : {"", "F", "FHMod", "FHMod999", "FHMod01000", "FHMod-1000", "FHMod2147483647",
                             "FHMod9999999999999", "FHMod1234_disabled", "fhmod1000", "3D Movie Maker"})
        EXPECT_EQ(ModSourceId(name), 0) << name;
}

TEST(ModSource, WorkshopNativeContainer)
{
    FNI fni;
    GetTestResource(&fni, PszLit("workshop-model.3cn"));
    PCFL pcfl = CFL::PcflOpen(&fni, fcflNil);
    ASSERT_NE(pcfl, pvNil);
    KID kid;
    EXPECT_TRUE(pcfl->FGetKidChidCtg(KLCONST4('T', 'M', 'P', 'L'), 1, 0, KLCONST4('B', 'M', 'D', 'L'), &kid));
    BLCK blck;
    ASSERT_TRUE(pcfl->FFind(KLCONST4('G', 'L', 'P', 'I'), 1, &blck));
    PGL pgl = GL::PglRead(&blck);
    ASSERT_NE(pgl, pvNil);
    EXPECT_EQ(pgl->IvMac(), 1);
    EXPECT_EQ(pgl->CbEntry(), 2);
    ReleasePpo(&pgl);
    ASSERT_TRUE(pcfl->FFind(KLCONST4('G', 'G', 'C', 'L'), 1, &blck));
    PGG pgg = GG::PggRead(&blck);
    ASSERT_NE(pgg, pvNil);
    EXPECT_EQ(pgg->IvMac(), 1);
    EXPECT_EQ(pgg->Cb(0), 4);
    ReleasePpo(&pgg);
    ReleasePpo(&pcfl);
}
