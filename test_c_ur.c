#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

// Include the UR decoder headers
#include "firmware/MaixPy/components/micropython/port/src/bc-ur/src/ur_decoder.h"

// Expected result for verification (243 bytes)
const char* expected_result = "y\x01@tr([65fb43fe/48'/1'/0'/2']tpubDFM6mziafLfJPA9StFuzvdC5htjaMTsVaPSAjsahgE4c2CMWpg9yKaK4JyoaBjVYJKUFX9Kdyb4fgFaFUQmZNGU71Q1wZgZiGM1Go7p59NW/<0;1>/*,and_v(v:pk([e9ce0106/48'/1'/0'/2']tpubDFKLfb2ribn4qhoCN1eKHRHK3wrvFzgW5Fx1PZ3P2Y3NQV7MWe9K9hL4B4bi3LB1ErJ5AYhAe4atTDGprxaHsgXBJFETt2boz4NA4Z7AZJp/<0;1>/*),older(2)))#9qmm4r5y";
const size_t expected_result_len = 243;

// Test vectors - complete set including duplicates from your login.py
const char* test_fragments[] = {
    // "ur:crypto-psbt/2-8/lpaoaycfadcycyamgrmswlhddkplkooncmswqdampahlvloyglaeaeaeaeaezczmzmzmaokefhhlahaeaeaeaecmaebbdleepktpcpnyde",
    // "ur:crypto-psbt/1-8/lpadaycfadcycyamgrmswlhddkhkadchjojkidjyzmadaejsaoaeaeaeadtkfnhdsrdtlfplcxgdlotarygawmndaopsurgtfswmwkinva",
    // "ur:crypto-psbt/3-8/lpaxaycfadcycyamgrmswlhddkcewtbkgupfgooemenbftkifewtolmklugmlamtmkaeaeaeaeaecmaebbvaimzezmsrlsmnjseylanegy",
    // "ur:crypto-psbt/4-8/lpaaaycfadcycyamgrmswlhddkwtoekgatvlpfbaueimvsvyhnaeaeaeaeaeadadctaevyykahaeaeaeaecmaebbtissotwsaskeisuold",
    // "ur:crypto-psbt/5-8/lpahaycfadcycyamgrmswlhddkwlmsrpwlnneskbgymyvlvecybylkoycpamaovdpydaemretynnmsaxaspkvtjtnngawfjzvychtbfxax",
    // "ur:crypto-psbt/6-8/lpamaycfadcycyamgrmswlhddksozerktyglspvtttsfnbqzytsrcfcsjksktnbkghaeaelaadaeaelaaeaeaelaaeaeaeaeaestwncstl",
    // "ur:crypto-psbt/7-8/lpataycfadcycyamgrmswlhddkaeaeaeaecpaoaxhlgawpsnghtiasnnfxioidktstoltyidhlhscapdlehlwkndytgyknktmevltdqzhn",
    // "ur:crypto-psbt/8-8/lpayaycfadcycyamgrmswlhddkosktoncsjksktnbkghaeaelaadaeaelaaeaeaelaadaeaeaeaeaeaeaeaeaeaeaeaeaeaeaefxktbtbb",
    "UR:BYTES/9-4/LPASAACFADFXCYCMRTFYMNHDGYFWEEIDINEOGSFWEHFEJPGEECFPHKISFPIHEEHSJYGHFYFLJOJPKSHSFDJKIOHDFWGEFGFEGHJYEYIDJLKNEEGLFPEEHTEMFPHTGEJODLFNDYFREHFMDLDRDTDWJLJZIEIHJPDEEYDTDTDTCNESJSJNJNEEJPECKKAEVDGUYLLR",
    "UR:BYTES/10-4/LPBKAACFADFXCYCMRTFYMNHDGYJOIOESKKGRHSGREEGEKKJLHSFWIMHFHKGEGRGOFGHDESGRIEKKIDEEIYIOFGHSFGGOGYJNHTGLFLGOEMEHGYEHKTHTIOHTINFLGTEHFLJLEMJOECESGLHGDLFNDYFREHFMDLDRDWHSJTIEHEKODEKOFTJOJEDEHPIHDYFSOTGH",
    "UR:BYTES/10-4/LPBKAACFADFXCYCMRTFYMNHDGYJOIOESKKGRHSGREEGEKKJLHSFWIMHFHKGEGRGOFGHDESGRIEKKIDEEIYIOFGHSFGGOGYJNHTGLFLGOEMEHGYEHKTHTIOHTINFLGTEHFLJLEMJOECESGLHGDLFNDYFREHFMDLDRDWHSJTIEHEKODEKOFTJOJEDEHPIHDYFSOTGH",
    "UR:BYTES/11-4/LPBDAACFADFXCYCMRTFYMNHDGYFWEEIDINEOGSFWEHFEJPGEECFPHKISFPIHEEHSJYGHFYFLJOJPKSHSFDJKIOHDFWGEFGFEGHJYEYIDJLKNEEGLFPEEHTEMFPHTGEJODLFNDYFREHFMDLDRDTDWJLJZIEIHJPDEEYDTDTDTCNESJSJNJNEEJPECKKAEFYTKSRRP",
    "UR:BYTES/12-4/LPBNAACFADFXCYCMRTFYMNHDGYKGHGATHKAOKEJYCKJSGEJNCYJOKBFLJSFWCWGUGUASDYEMAHBEFNDIAXFHADFTJOETDLDIFTFZFXBKAEESKNLBDKLBBGIHASBYKKATHLGEKOFPHFINCYJZGYCAFHENHGECFZJSADIOKSLBBBJYDSAYGHLBGRHLECEEDIKOFMLF",
    "UR:BYTES/12-4/LPBNAACFADFXCYCMRTFYMNHDGYKGHGATHKAOKEJYCKJSGEJNCYJOKBFLJSFWCWGUGUASDYEMAHBEFNDIAXFHADFTJOETDLDIFTFZFXBKAEESKNLBDKLBBGIHASBYKKATHLGEKOFPHFINCYJZGYCAFHENHGECFZJSADIOKSLBBBJYDSAYGHLBGRHLECEEDIKOFMLF",
    "UR:BYTES/13-4/LPBTAACFADFXCYCMRTFYMNHDGYESIAIHDYEHDYENDLEEETDIDLEHDIDLDYDIDLEYDIHLJYJOKPIDFYFGGRGSIYIDEYJPINIDJTEEJSISJLFXGLEHIHGRFDGMFDGREOKTJPKOFGKNIOHGECFGKSEHGDHTEOGDEYHKEOGLGYHFEMGTHGIHESGRESISGSEENYFYFXMT",
    "UR:BYTES/13-4/LPBTAACFADFXCYCMRTFYMNHDGYESIAIHDYEHDYENDLEEETDIDLEHDIDLDYDIDLEYDIHLJYJOKPIDFYFGGRGSIYIDEYJPINIDJTEEJSISJLFXGLEHIHGRFDGMFDGREOKTJPKOFGKNIOHGECFGKSEHGDHTEOGDEYHKEOGLGYHFEMGTHGIHESGRESISGSEENYFYFXMT",
    "UR:BYTES/14-4/LPBAAACFADFXCYCMRTFYMNHDGYEYGUHPBEKSDPASAHBSBDDAGHAXEOFMCSDLLBEEEYBNKIBNBBBDCYGODMBBCLESAACTCHDEBAFTKPEMHDGRIHLBENJTFSJNDECAATFPISGUATGRAAATHSKIAMBEHEHGGOHPHLAOCKFDFLGTKEGWHKCWHGFYCFCACPIHFZLOPKKE",
    "UR:BYTES/14-4/LPBAAACFADFXCYCMRTFYMNHDGYEYGUHPBEKSDPASAHBSBDDAGHAXEOFMCSDLLBEEEYBNKIBNBBBDCYGODMBBCLESAACTCHDEBAFTKPEMHDGRIHLBENJTFSJNDECAATFPISGUATGRAAATHSKIAMBEHEHGGOHPHLAOCKFDFLGTKEGWHKCWHGFYCFCACPIHFZLOPKKE",
    "UR:BYTES/15-4/LPBSAACFADFXCYCMRTFYMNHDGYFWEEIDINEOGSFWEHFEJPGEECFPHKISFPIHEEHSJYGHFYFLJOJPKSHSFDJKIOHDFWGEFGFEGHJYEYIDJLKNEEGLFPEEHTEMFPHTGEJODLFNDYFREHFMDLDRDTDWJLJZIEIHJPDEEYDTDTDTCNESJSJNJNEEJPECKKAETPLNPMMU",
    "UR:BYTES/15-4/LPBSAACFADFXCYCMRTFYMNHDGYFWEEIDINEOGSFWEHFEJPGEECFPHKISFPIHEEHSJYGHFYFLJOJPKSHSFDJKIOHDFWGEFGFEGHJYEYIDJLKNEEGLFPEEHTEMFPHTGEJODLFNDYFREHFMDLDRDTDWJLJZIEIHJPDEEYDTDTDTCNESJSJNJNEEJPECKKAETPLNPMMU",
    "UR:BYTES/16-4/LPBEAACFADFXCYCMRTFYMNHDGYEYGUHPBEKSDPASAHBSBDDAGHAXEOFMCSDLLBEEEYBNKIBNBBBDCYGODMBBCLESAACTCHDEBAFTKPEMHDGRIHLBENJTFSJNDECAATFPISGUATGRAAATHSKIAMBEHEHGGOHPHLAOCKFDFLGTKEGWHKCWHGFYCFCACPIHLAAYMKEM",
    "UR:BYTES/16-4/LPBEAACFADFXCYCMRTFYMNHDGYEYGUHPBEKSDPASAHBSBDDAGHAXEOFMCSDLLBEEEYBNKIBNBBBDCYGODMBBCLESAACTCHDEBAFTKPEMHDGRIHLBENJTFSJNDECAATFPISGUATGRAAATHSKIAMBEHEHGGOHPHLAOCKFDFLGTKEGWHKCWHGFYCFCACPIHLAAYMKEM",
    "UR:BYTES/17-4/LPBYAACFADFXCYCMRTFYMNHDGYJPEHKBGHFRECIECEBAGOHNGWADJPJYATFNISCLFTHNDMGUGYGLJSCLFWAHEODNFXBSFTBNDPETINDAHYINGTAOECJLDAKBHKAHFZJOJLHEEMGOCXIHFNGWBBFZFWHKBZHLBABDKBFLKEISDRIMINFRHTJZBGENCNAMCSBGAYFR",
    "UR:BYTES/17-4/LPBYAACFADFXCYCMRTFYMNHDGYJPEHKBGHFRECIECEBAGOHNGWADJPJYATFNISCLFTHNDMGUGYGLJSCLFWAHEODNFXBSFTBNDPETINDAHYINGTAOECJLDAKBHKAHFZJOJLHEEMGOCXIHFNGWBBFZFWHKBZHLBABDKBFLKEISDRIMINFRHTJZBGENCNAMCSBGAYFR",
    "UR:BYTES/18-4/LPBGAACFADFXCYCMRTFYMNHDGYJPEHKBGHFRECIECEBAGOHNGWADJPJYATFNISCLFTHNDMGUGYGLJSCLFWAHEODNFXBSFTBNDPETINDAHYINGTAOECJLDAKBHKAHFZJOJLHEEMGOCXIHFNGWBBFZFWHKBZHLBABDKBFLKEISDRIMINFRHTJZBGENCNAMWDFZDSBE",
    "UR:BYTES/18-4/LPBGAACFADFXCYCMRTFYMNHDGYJPEHKBGHFRECIECEBAGOHNGWADJPJYATFNISCLFTHNDMGUGYGLJSCLFWAHEODNFXBSFTBNDPETINDAHYINGTAOECJLDAKBHKAHFZJOJLHEEMGOCXIHFNGWBBFZFWHKBZHLBABDKBFLKEISDRIMINFRHTJZBGENCNAMWDFZDSBE",
    "UR:BYTES/19-4/LPBWAACFADFXCYCMRTFYMNHDGYBDDYFMCXGACAFHDRFREOAOKGEYBBBYDEAYGDAMBZGYASKEHSINHYBWIHHDFLHPENJNKBGEHNBAAAHEEMAYDNGLGUDAKPFHHNHFEEENCYDAFPEHIAGDGHFRKBCLBSBTIYBDJLHPDPAMCMCWGRAOBAKBJTBSCXKPJTGYLBYABDDS",
    "UR:BYTES/19-4/LPBWAACFADFXCYCMRTFYMNHDGYBDDYFMCXGACAFHDRFREOAOKGEYBBBYDEAYGDAMBZGYASKEHSINHYBWIHHDFLHPENJNKBGEHNBAAAHEEMAYDNGLGUDAKPFHHNHFEEENCYDAFPEHIAGDGHFRKBCLBSBTIYBDJLHPDPAMCMCWGRAOBAKBJTBSCXKPJTGYLBYABDDS",
    "UR:BYTES/20-4/LPBBAACFADFXCYCMRTFYMNHDGYEYGUHPBEKSDPASAHBSBDDAGHAXEOFMCSDLLBEEEYBNKIBNBBBDCYGODMBBCLESAACTCHDEBAFTKPEMHDGRIHLBENJTFSJNDECAATFPISGUATGRAAATHSKIAMBEHEHGGOHPHLAOCKFDFLGTKEGWHKCWHGFYCFCACPIHCEFPYNBG",
    "UR:BYTES/20-4/LPBBAACFADFXCYCMRTFYMNHDGYEYGUHPBEKSDPASAHBSBDDAGHAXEOFMCSDLLBEEEYBNKIBNBBBDCYGODMBBCLESAACTCHDEBAFTKPEMHDGRIHLBENJTFSJNDECAATFPISGUATGRAAATHSKIAMBEHEHGGOHPHLAOCKFDFLGTKEGWHKCWHGFYCFCACPIHCEFPYNBG",
    "UR:BYTES/21-4/LPBZAACFADFXCYCMRTFYMNHDGYKGHGATHKAOKEJYCKJSGEJNCYJOKBFLJSFWCWGUGUASDYEMAHBEFNDIAXFHADFTJOETDLDIFTFZFXBKAEESKNLBDKLBBGIHASBYKKATHLGEKOFPHFINCYJZGYCAFHENHGECFZJSADIOKSLBBBJYDSAYGHLBGRHLECEELDWEGSST",
    "UR:BYTES/21-4/LPBZAACFADFXCYCMRTFYMNHDGYKGHGATHKAOKEJYCKJSGEJNCYJOKBFLJSFWCWGUGUASDYEMAHBEFNDIAXFHADFTJOETDLDIFTFZFXBKAEESKNLBDKLBBGIHASBYKKATHLGEKOFPHFINCYJZGYCAFHENHGECFZJSADIOKSLBBBJYDSAYGHLBGRHLECEELDWEGSST",
};

int main() {
    printf("=== C UR Decoder Test ===\n");
    printf("Testing with %zu fragments\n", sizeof(test_fragments) / sizeof(test_fragments[0]));

    // Create decoder
    ur_decoder_t* decoder = ur_decoder_new();
    if (!decoder) {
        printf("ERROR: Failed to create UR decoder\n");
        return 1;
    }

    printf("✓ UR decoder created successfully\n");

    // Process each fragment
    for (size_t i = 0; i < sizeof(test_fragments) / sizeof(test_fragments[0]); i++) {
        printf("\n--- Processing fragment %zu/%zu ---\n", i + 1, sizeof(test_fragments) / sizeof(test_fragments[0]));
        printf("Fragment: %.60s...\n", test_fragments[i]);

        bool success = ur_decoder_receive_part(decoder, test_fragments[i]);
        bool complete = ur_decoder_is_complete(decoder);
        double progress = ur_decoder_estimated_percent_complete(decoder);

        printf("Success: %s\n", success ? "true" : "false");
        printf("Complete: %s\n", complete ? "true" : "false");
        printf("Progress: %.1f%%\n", progress * 100.0);

        if (complete) {
            printf("🎉 Decoder completed!\n");

            if (ur_decoder_is_success(decoder)) {
                ur_result_t* result = ur_decoder_get_result(decoder);
                if (result && result->cbor_data) {
                    printf("✓ Decoding successful!\n");
                    printf("Result length: %zu bytes\n", result->cbor_len);
                    printf("First 16 bytes: ");
                    for (size_t j = 0; j < 16 && j < result->cbor_len; j++) {
                        printf("%02x ", result->cbor_data[j]);
                    }
                    printf("\n");

                    // Check if result matches expected
                    if (result->cbor_len == expected_result_len &&
                        memcmp(result->cbor_data, expected_result, expected_result_len) == 0) {
                        printf("✅ RESULT MATCHES EXPECTED OUTPUT!\n");
                    } else {
                        printf("❌ Result does not match expected output\n");
                        printf("Expected length: %zu, got: %zu\n", expected_result_len, result->cbor_len);
                        printf("Expected first 32 bytes: ");
                        for (size_t j = 0; j < 32 && j < expected_result_len; j++) {
                            printf("%02x ", (uint8_t)expected_result[j]);
                        }
                        printf("\n");
                        printf("Actual first 32 bytes:   ");
                        for (size_t j = 0; j < 32 && j < result->cbor_len; j++) {
                            printf("%02x ", result->cbor_data[j]);
                        }
                        printf("\n");

                        // Show full message for comparison if reasonable size
                        if (result->cbor_len <= 400) {
                            printf("Full actual message: ");
                            for (size_t j = 0; j < result->cbor_len; j++) {
                                if (result->cbor_data[j] >= 32 && result->cbor_data[j] <= 126) {
                                    printf("%c", result->cbor_data[j]);
                                } else {
                                    printf("\\x%02x", result->cbor_data[j]);
                                }
                            }
                            printf("\n");

                            printf("Expected message: ");
                            for (size_t j = 0; j < expected_result_len; j++) {
                                if (expected_result[j] >= 32 && expected_result[j] <= 126) {
                                    printf("%c", expected_result[j]);
                                } else {
                                    printf("\\x%02x", expected_result[j]);
                                }
                            }
                            printf("\n");
                        }
                    }
                } else {
                    printf("❌ No result data available\n");
                }
            } else {
                printf("❌ Decoder completed with failure\n");
                ur_decoder_error_t error = ur_decoder_get_last_error(decoder);
                printf("Error code: %d\n", error);
            }
            break;
        }
    }

    if (!ur_decoder_is_complete(decoder)) {
        printf("\n❌ Decoder did not complete after all fragments\n");
        printf("Final progress: %.1f%%\n", ur_decoder_estimated_percent_complete(decoder) * 100.0);
        ur_decoder_error_t error = ur_decoder_get_last_error(decoder);
        printf("Last error: %d\n", error);
    }

    // Cleanup
    ur_decoder_free(decoder);
    printf("\n✓ Test completed, decoder freed\n");

    return 0;
}