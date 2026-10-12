// 자동 생성: site/tools/build_site.py 가 사이트 코드에서 그대로 복사함. 직접 고치지 말 것.
const KoreanLunarCalendar = (()=>{
//#region src/korean-lunar-data.ts
var LUNAR_CALENDAR_DATA = {
	KOREAN_LUNAR_MIN_VALUE: 10000101,
	KOREAN_LUNAR_MAX_VALUE: 20501118,
	KOREAN_SOLAR_MIN_VALUE: 10000213,
	KOREAN_SOLAR_MAX_VALUE: 20501231,
	KOREAN_LUNAR_BASE_YEAR: 1e3,
	SOLAR_LUNAR_DAY_DIFF: 43,
	LUNAR_SMALL_MONTH_DAY: 29,
	LUNAR_BIG_MONTH_DAY: 30,
	SOLAR_SMALL_YEAR_DAY: 365,
	SOLAR_BIG_YEAR_DAY: 366,
	SOLAR_DAYS: [
		31,
		28,
		31,
		30,
		31,
		30,
		31,
		31,
		30,
		31,
		30,
		31,
		29
	],
	KOREAN_CHEONGAN: [
		44049,
		51012,
		48337,
		51221,
		47924,
		44592,
		44221,
		49888,
		51076,
		44228
	].map((c) => String.fromCharCode(c)),
	KOREAN_GANJI: [
		51088,
		52629,
		51064,
		47896,
		51652,
		49324,
		50724,
		48120,
		49888,
		50976,
		49696,
		54644
	].map((c) => String.fromCharCode(c)),
	KOREAN_GAPJA_UNIT: [
		45380,
		50900,
		51068
	].map((c) => String.fromCharCode(c)),
	CHINESE_CHEONGAN: [
		30002,
		20057,
		19993,
		19969,
		25098,
		24049,
		24218,
		36763,
		22764,
		30328
	].map((c) => String.fromCharCode(c)),
	CHINESE_GANJI: [
		23376,
		19985,
		23493,
		21359,
		36784,
		24051,
		21320,
		26410,
		30003,
		37193,
		25100,
		20133
	].map((c) => String.fromCharCode(c)),
	CHINESE_GAPJA_UNIT: [
		24180,
		26376,
		26085
	].map((c) => String.fromCharCode(c)),
	INTERCALATION_STR: [50980, 38287].map((c) => String.fromCharCode(c)),
	KOREAN_LUNAR_DATA: [
		2194016855,
		2197734699,
		2193886506,
		2194017621,
		3271595437,
		2193884522,
		2194016621,
		2197837021,
		3267626157,
		2193885773,
		2197827149,
		2193885990,
		3271600982,
		2194016981,
		2193883994,
		2197842298,
		3267758427,
		2193884315,
		2197834395,
		2193885771,
		3271674533,
		2193884842,
		2194016981,
		2197852893,
		3267625653,
		2194016599,
		2197705902,
		2194017431,
		3267626571,
		2197759306,
		2194017705,
		2197857974,
		3267757677,
		2193883758,
		2197907758,
		2193885486,
		3267628182,
		2197835157,
		2193886538,
		2197867881,
		3267627864,
		2194148715,
		2197918315,
		2193883741,
		3267627307,
		2197838507,
		2193885845,
		2193886026,
		3271696043,
		2193883861,
		2197927258,
		2194015419,
		3267625563,
		2197845303,
		2193884459,
		2193884821,
		3271571285,
		2193884842,
		2198063797,
		2193883765,
		3267626166,
		2197850718,
		2193885782,
		2193886502,
		3271581350,
		2194017621,
		2193884586,
		2197822826,
		3267758445,
		2197861551,
		2193884317,
		2193885773,
		3271589165,
		2193885862,
		2194017109,
		2197833173,
		3267625818,
		2194016605,
		2197885299,
		2193884251,
		3271596623,
		2193884747,
		2193885861,
		2197842793,
		3267757749,
		2193883866,
		2197826230,
		2194016567,
		3271476375,
		2194017431,
		2193884747,
		2197718698,
		3267759525,
		2193884596,
		2198030957,
		2193883822,
		3267628641,
		2197826862,
		2193886358,
		2197855565,
		2193886538,
		2194017637,
		2197906837,
		2194015581,
		3267625581,
		2197826141,
		2193885483,
		2197858967,
		3267627669,
		2193886026,
		2197850970,
		2194016981,
		3267757403,
		2197832375,
		2193884247,
		2193884459,
		3271564587,
		2193884821,
		2197853997,
		2193884586,
		3267758773,
		2197837037,
		2193884342,
		2194016855,
		3271504974,
		2193886502,
		2197929618,
		2194017621,
		3267626410,
		2197850554,
		2194016621,
		2193884334,
		3271576221,
		2193885773,
		2193886501,
		2197827365,
		3267627860,
		2198056297,
		2193883866,
		2194016605,
		3271648411,
		2193884315,
		2193885771,
		2197834571,
		3267626661,
		2197863251,
		2193884852,
		2194016950,
		3271657814,
		2194016663,
		2193884311,
		2197833367,
		3267626315,
		2197735077,
		2194017701,
		2193884588,
		3271797429,
		2193883758,
		2193885486,
		2197843118,
		3267628182,
		2193886538,
		2197827402,
		2194017621,
		3271603563,
		2194015579,
		2193883741,
		2197846333,
		3267627303,
		2193885845,
		2197904661,
		2193886026,
		3267758933,
		2197885653,
		2194015451,
		2197721694,
		3267758679,
		2193884459,
		2197842603,
		2193884821,
		3267626666,
		2197830570,
		2194016949,
		2197861559,
		3267626158,
		2194016855,
		2197714222,
		2193886502,
		3267759763,
		2197837525,
		2193884586,
		2194016693,
		3271566701,
		2193884334,
		2197924429,
		2193885773,
		3267628326,
		2197843301,
		2193886034,
		2194017642,
		3271567066,
		2194016605,
		2197931165,
		2193884315,
		3267627595,
		2197850795,
		2193884837,
		2193886036,
		3271576500,
		2194016950,
		2194016603,
		2197824823,
		3267626135,
		2197853775,
		2193884491,
		2193884837,
		3271653061,
		2193884588,
		2194016950,
		2197895278,
		3267627310,
		2197867671,
		2193886358,
		2193886538,
		3271593386,
		2194017109,
		2193884522,
		2197969627,
		3267625565,
		2193885486,
		2197826859,
		2193885845,
		3271597389,
		2193885994,
		2194017109,
		2197845365,
		3267626202,
		2194016859,
		2197833047,
		2193884459,
		3271674515,
		2193884819,
		2193884842,
		2197850842,
		3267758821,
		2193884342,
		2197834414,
		2194016855,
		3267626279,
		2197759270,
		2194017875,
		2197857995,
		3267626410,
		2194015661,
		2197906605,
		2193884334,
		3267627598,
		2197835085,
		2193886502,
		2197863763,
		3267627858,
		2194017130,
		2197919082,
		2194015575,
		3267626141,
		2197903899,
		2193885771,
		2193885861,
		3271564965,
		2193886034,
		2197863258,
		2194016950,
		3267758427,
		2197841079,
		2193884311,
		2193884747,
		3271571275,
		2193884837,
		2197862067,
		2193884588,
		3267758774,
		2197914285,
		2193884318,
		2193885773,
		3271581003,
		2193885989,
		2193886034,
		2197892690,
		3267758938,
		2197858654,
		2194016603,
		2193884315,
		3271584343,
		2193885771,
		2193885861,
		2197834661,
		3267626708,
		2197867222,
		2194016950,
		2194016567,
		2197849247,
		2193884311,
		2193884747,
		2197706442,
		3267759525,
		2193884586,
		2197822828,
		2194016878,
		3271604527,
		2193885486,
		2193886358,
		2197847381,
		3267628362,
		2194017621,
		2197894485,
		2193884522,
		3267758701,
		2197822045,
		2193885483,
		2197850715,
		3267627669,
		2193885994,
		2197904170,
		2194016981,
		3267626202,
		2197822650,
		2194016855,
		2197853487,
		3267626279,
		2193884819,
		2197845683,
		2193884842,
		3267758773,
		2197828981,
		2193884342,
		2197867111,
		3267627566,
		2193886486,
		2197851798,
		2193886538,
		3267759530,
		2197837290,
		2194015597,
		2193884334,
		3271632989,
		2193885741,
		2197859607,
		2193885861,
		3267627858,
		2197847412,
		2194016986,
		2194015581,
		3271570747,
		2193884251,
		2193885739,
		2197887531,
		3267627685,
		2197855061,
		2193884850,
		2194016982,
		3271644470,
		2194016567,
		2193884247,
		2197830231,
		3267626283,
		2197727910,
		2194017685,
		2193884586,
		3271654060,
		2194016878,
		2193884462,
		2197830830,
		3267627606,
		2197863723,
		2193886506,
		2194017621,
		3271595437,
		2193884522,
		2194016877,
		2197837149,
		3267626283,
		2193885837,
		2197827157,
		2193885994,
		3271600982,
		2194016981,
		2193884378,
		2197842554,
		3267758679,
		2193884443,
		2197899799,
		2193884755,
		3271673513,
		2193884586,
		2194016949,
		2197852861,
		3267625654,
		2194016823,
		2197706030,
		2193886486,
		2194017867,
		2197698386,
		2194017706,
		2197927348,
		3267757421,
		2193883822,
		2197846589,
		2193885741,
		3267628309,
		2197835157,
		2193886034,
		2197867369,
		3267758810,
		2194015581,
		2197918299,
		2193884251,
		3267627563,
		2197838507,
		2193885845,
		2193886034,
		3271564970,
		2194016950,
		2197865819,
		2194015415,
		3267626071,
		2197845303,
		2193884459,
		2193884821,
		3271640725,
		2193884586,
		2197867189,
		2194016878,
		3267626158,
		2197850718,
		2193885782,
		2193886506,
		3271585450,
		2194017621,
		2193884522,
		2197891418,
		3267758429,
		2197861551,
		2193884315,
		2193885773,
		3271589165,
		2193885994,
		2194017109,
		2197833173,
		3267625690,
		2194016603,
		2197885271,
		2193884315,
		3271596623,
		2193884747,
		2193884841,
		2197842666,
		3267757749,
		2193883830,
		2197826222,
		2194016567,
		3271537814,
		2193886358,
		2194017867,
		2197714610,
		3267759530,
		2194015661,
		2197828461,
		2193883758,
		3267627310,
		2197826861,
		2193886357,
		2197855565,
		3267627850,
		2194017129,
		2197906778,
		2194015579,
		3267625565,
		2197826139,
		2193885483,
		2197858967,
		3267626645,
		2193885002,
		2197850970,
		2194016950,
		3267757371,
		2197832375,
		2193883735,
		2193884459,
		3271564587,
		2193884821,
		2197853869,
		2193884586,
		3267758773,
		2197837037,
		2193884334,
		2194016855,
		3271504974,
		2193886506,
		2197929364,
		2194017109,
		2193884522,
		2197846394,
		2194016605,
		2193884334,
		3271576219,
		2193885773,
		2193886501,
		2197887658,
		3267758933,
		2197853549,
		2193883866,
		2194016603,
		3271578807,
		2193884311,
		2193885771,
		2197834571,
		3267626665,
		2197867221,
		2194015669,
		2193883830,
		3271592286,
		2194016559,
		2193884311,
		2197702294,
		3267628362,
		2197868197,
		2194017641,
		2194015597,
		3271664309,
		2193883758,
		2193885486,
		2197843117,
		3267628181,
		2193886538,
		2197827402,
		2194017113,
		3271607661,
		2194015579,
		2193883741,
		2197846331,
		3267627307,
		2193885845,
		2197904149,
		2193884874,
		3267758805,
		2197885622,
		2194015419,
		2197852767,
		3267625559,
		2193884459,
		2197711530,
		2194017941,
		3267626666,
		2197830570,
		2194016949,
		2197861559,
		3267626158,
		2194016855,
		2197714221,
		2193886502,
		3267759509,
		2197837269,
		2193884522,
		2194016621,
		3271566685,
		2193884334,
		2197858895,
		2193885773,
		3267628325,
		2197843305,
		2194017109,
		2193883994,
		3271568058,
		2194016603,
		2197931163,
		2193884311,
		3267627595,
		2197850923,
		2193884837,
		2193884884,
		3271772853,
		2193883830,
		2194016567,
		2197824815,
		3267626135,
		2197722702,
		2193886538,
		2194017957,
		3271648937,
		2194015597,
		2193883830,
		2197895262,
		3267627310,
		2197863575,
		2193885845,
		2193886538,
		3271593386,
		2194017101,
		2194015595,
		2197832411,
		3267625565,
		2193885485,
		2197826859,
		2193885845,
		3271596877,
		2193884842,
		2194016981,
		2197841269,
		3267757243,
		2193883739,
		2197894231,
		2193884459,
		3271539348,
		2194017941,
		2193884842,
		2197850842,
		3267758517,
		2193884342,
		2197834414,
		2194016847,
		3267495206,
		2197892390,
		2194017621,
		2197923241,
		3267626346,
		2194016621,
		2197906589,
		2193884318,
		3267627597,
		2197835085,
		2193886501,
		2197863763,
		3267627860,
		2194017114,
		2197915994,
		2194016603,
		3267626139,
		2197834391,
		2193885771,
		2193885861,
		3271564965,
		2193884884,
		2197994203,
		2193883830,
		3267758391,
		2197841071,
		2193884311,
		2193884747,
		3271440202,
		2194017701,
		2197862069,
		2194015597,
		3267625646,
		2197846334,
		2193885486,
		2193886358,
		3271646485,
		2193886538,
		2194017701,
		2197894485,
		3267626346,
		2197846650,
		2194016861,
		2193885485,
		3271584427,
		2193885845,
		2193886026,
		2197834666,
		3267758805,
		2193884506,
		2197891258,
		2194016859,
		3271587127,
		2193884459,
		2193884819,
		2197903125,
		3267626666,
		2194016981,
		2197829045,
		2193884342,
		3271592542,
		2193885774,
		2193886502,
		2197843622,
		3267628370,
		2194017706,
		2197898858,
		2194015597,
		3267626158,
		2197830301,
		2193885773,
		2197847339,
		3267627813,
		2193886546,
		2197904724,
		2194017114,
		3267757405,
		2197828955,
		2193884315,
		2197845591,
		2193885771,
		2193885861,
		2197842789,
		2193884882,
		3267758810,
		2197833142,
		2194016567,
		2193884311,
		3271571095,
		2193884749,
		2197714602,
		2194017701,
		3267626410,
		2197838572,
		2194016942,
		2193885486,
		3271572782,
		2193886358,
		2197916997,
		2193886538,
		3267759445,
		2197906837,
		2193884522,
		2194016877,
		3271574877,
		2193884461,
		2193885845,
		2197896341,
		3267627850,
		2197912394,
		2194016981,
		2193884506,
		3271645754,
		2194016859,
		2193884459,
		2197899799,
		3267626643,
		2197853867,
		2193884842,
		2194016949,
		3271582965,
		2193884342,
		2194016855,
		2197701934,
		3267628310,
		2194017939,
		2197698386,
		2194017706,
		3271652778,
		2194015597,
		2193884334,
		2197903901,
		3267627565,
		2193886485,
		2197835173,
		2193886034,
		3271597418,
		2194016986,
		2194015581,
		2197906075,
		3267626075,
		2193885739,
		2197838635,
		2193885845,
		3267627858,
		2197891762,
		2194016982,
		2197910870,
		3267757367,
		2193884247,
		2197837399,
		2193884459,
		3267626645,
		2197829525,
		2193884586,
		2197858998,
		3267758701,
		2193884334,
		2197842542,
		2193885782,
		3267628330,
		2197839530,
		2194017621,
		2193884586,
		3271572330,
		2194016877,
		2197845181,
		2193884331,
		3267627661,
		2197839189,
		2193885994,
		2194017109,
		3271574997,
		2193884378,
		2194016605,
		2197824855,
		3267626139,
		2197842583,
		2193884747,
		2193884841,
		2197834666,
		2194015925,
		2193883834,
		2197826230,
		3267758391,
		2197710126,
		2193886486,
		2194017867,
		3271448274,
		2194017705,
		2194015669,
		2197828461,
		3267625646,
		2193885742,
		2197827117,
		2193886357,
		3271585109,
		2193886034,
		2194017129,
		2197833178,
		3267757405,
		2193883741,
		2197830235,
		2193885739,
		3271654027,
		2193885845,
		2193886026,
		2197904170,
		3267758805,
		2194015579,
		2197832375,
		2193883735,
		3271595311,
		2193884459,
		2193884821,
		2197841621,
		3267626410,
		2194016949,
		2197833069,
		2193884334,
		3267758679,
		2197763158,
		2193886506,
		2197913226,
		3267759445,
		2193884586,
		2197838554,
		2194016605,
		3267626158,
		2197834411,
		2193885773,
		2197851435,
		3267627817,
		2194017109,
		2197845365,
		2193883866,
		3267758429,
		2197837015,
		2193884315,
		2193885771,
		3271637579,
		2193884841,
		2197850841,
		2194015925,
		3267625654,
		2197903670,
		2194016567,
		2193884311,
		3271444118,
		2193886794,
		2197860006,
		2194017705,
		3267757485,
		2197906093,
		2193883822,
		2193885486,
		3271580845,
		2193886357,
		2193886538,
		2197896522,
		3267758953,
		2197845370,
		2194015579,
		2193883741,
		3271579995,
		2193885483,
		2193885845,
		2197835157,
		3267627850,
		2194017109,
		2197825237,
		2194015579,
		3271582327,
		2193883735,
		2193884459,
		2197707434,
		3267759765,
		2193884842,
		2197830570,
		2194016949,
		2197849277,
		2193884334,
		2194016855,
		2197706061,
		3267628326,
		2194017685,
		2197898837,
		2193884522,
		3267758509,
		2197824861,
		2193884334,
		2197842523,
		3267627597,
		2193886501,
		2197839273,
		2194017109,
		3267626346,
		2197826266,
		2194016605,
		2197845179,
		3267626139,
		2193885771,
		2197838667,
		2193884841,
		3267627732,
		2197965749,
		2193883830,
		2194016603,
		3271566647,
		2193884311,
		2197710422,
		2193886794,
		3267759781,
		2197903017,
		2194015669,
		2193883830,
		3271637166,
		2193885486,
		2197912717,
		2193886357,
		3267628362,
		2197908874,
		2194017129,
		2194015597,
		3271639643,
		2193883741,
		2193885485,
		2197826859,
		3267627669,
		2197847381,
		2193886026,
		2194017109,
		3271644501,
		2194015451,
		2193883739,
		2197895255,
		3267626283,
		2197850779,
		2193884821,
		2193884842,
		3271584490,
		2194016949,
		2193884342,
		2197834414,
		3267758679,
		2193884455,
		2197698342,
		2194017685,
		3271587509,
		2193884522,
		2194016685,
		2197837021,
		3267626158,
		2193885774,
		2197835085,
		2193886501,
		3271593305,
		2193886036,
		2194017642,
		2197907802,
		3267758427,
		2193884315,
		2197834395,
		2193885771,
		3271600935,
		2193884837,
		2193884884,
		2197973877,
		3267625654,
		2194016603,
		2197836983,
		2193884311,
		3267626571,
		2197698378,
		2194017957,
		2197849817,
		3267757485,
		2193883830,
		2197838190,
		2193885486,
		3267628182,
		2197835413,
		2193886538,
		2194017701,
		3271567189,
		2193884524,
		2197977787,
		2193883741,
		3267627309,
		2197839019,
		2193885845,
		2193886026,
		3271637834,
		2194017109,
		2197853533,
		2193884346,
		3267758683,
		2197837143,
		2193884459,
		2193885845,
		3271576469,
		2193884842,
		2194016981,
		2197825205,
		3267626166,
		2197842542,
		2194016855,
		2193884455,
		3271448230,
		2194017683,
		2193884586,
		2197830506,
		3267758445,
		2197861551,
		2193884334,
		2193885773,
		3271650573,
		2193886501,
		2193886546,
		2197839316,
		3267758954,
		2194016621,
		2197824859,
		2193884315,
		3271588439,
		2193885771,
		2193885989,
		2197904165,
		3267626708,
		2194016986,
		2197895350
	]
};
//#endregion
//#region src/korean-lunar-calendar.ts
var GAPJA_OFFSET = {
	YEAR_CHEONGAN: 6,
	YEAR_GANJI: 0,
	MONTH_CHEONGAN: 3,
	MONTH_GANJI: 1,
	DAY_CHEONGAN: 4,
	DAY_GANJI: 2
};
var KoreanLunarCalendar = class {
	constructor() {
		this.cumulativeLunarYearDays = /* @__PURE__ */ new Map();
		this.cumulativeSolarYearDays = /* @__PURE__ */ new Map();
		this.solarCalendar = {
			year: 0,
			month: 0,
			day: 0
		};
		this.lunarCalendar = {
			year: 0,
			month: 0,
			day: 0,
			intercalation: false
		};
		const today = /* @__PURE__ */ new Date();
		this.setSolarDate(today.getFullYear(), today.getMonth() + 1, today.getDate());
	}
	getLunarData(year) {
		return LUNAR_CALENDAR_DATA.KOREAN_LUNAR_DATA[year - LUNAR_CALENDAR_DATA.KOREAN_LUNAR_BASE_YEAR];
	}
	getLunarIntercalationMonth(lunarData) {
		return lunarData >> 12 & 15;
	}
	getLunarYearDays(year) {
		return this.getLunarData(year) >> 17 & 511;
	}
	getLunarMonthDays(year, month, isIntercalation) {
		const lunarData = this.getLunarData(year);
		return (isIntercalation && this.getLunarIntercalationMonth(lunarData) === month ? (lunarData >> 16 & 1) > 0 : (lunarData >> 12 - month & 1) > 0) ? LUNAR_CALENDAR_DATA.LUNAR_BIG_MONTH_DAY : LUNAR_CALENDAR_DATA.LUNAR_SMALL_MONTH_DAY;
	}
	getLunarDaysBeforeBaseYear(year) {
		return this.accumulateYearDays(year, this.cumulativeLunarYearDays, (y) => this.getLunarYearDays(y));
	}
	getLunarDaysBeforeBaseMonth(year, month, isIntercalation) {
		let days = 0;
		if (year >= LUNAR_CALENDAR_DATA.KOREAN_LUNAR_BASE_YEAR && month > 0) {
			for (let baseMonth = 1; baseMonth < month + 1; baseMonth++) days += this.getLunarMonthDays(year, baseMonth, false);
			if (isIntercalation) {
				const intercalationMonth = this.getLunarIntercalationMonth(this.getLunarData(year));
				if (intercalationMonth > 0 && intercalationMonth < month + 1) days += this.getLunarMonthDays(year, intercalationMonth, true);
			}
		}
		return days;
	}
	getLunarAbsDays(year, month, day, isIntercalation) {
		let days = this.getLunarDaysBeforeBaseYear(year - 1) + this.getLunarDaysBeforeBaseMonth(year, month - 1, true) + day;
		if (isIntercalation && this.getLunarIntercalationMonth(this.getLunarData(year)) === month) days += this.getLunarMonthDays(year, month, false);
		return days;
	}
	isSolarIntercalationYear(lunarData) {
		return (lunarData >> 30 & 1) > 0;
	}
	getSolarYearDays(year) {
		return this.isSolarIntercalationYear(this.getLunarData(year)) ? LUNAR_CALENDAR_DATA.SOLAR_BIG_YEAR_DAY : LUNAR_CALENDAR_DATA.SOLAR_SMALL_YEAR_DAY;
	}
	getSolarMonthDays(year, month) {
		if (month === 2 && this.isSolarIntercalationYear(this.getLunarData(year))) return LUNAR_CALENDAR_DATA.SOLAR_DAYS[12];
		return LUNAR_CALENDAR_DATA.SOLAR_DAYS[month - 1];
	}
	getSolarDaysBeforeBaseYear(year) {
		return this.accumulateYearDays(year, this.cumulativeSolarYearDays, (y) => this.getSolarYearDays(y));
	}
	accumulateYearDays(year, cache, perYear) {
		const cached = cache.get(year);
		if (cached !== void 0) return cached;
		const baseYear = LUNAR_CALENDAR_DATA.KOREAN_LUNAR_BASE_YEAR;
		const previous = cache.get(year - 1);
		let days = 0;
		if (previous !== void 0 && year > baseYear) days = previous + perYear(year);
		else for (let y = baseYear; y < year + 1; y++) days += perYear(y);
		cache.set(year, days);
		return days;
	}
	getSolarDaysBeforeBaseMonth(year, month) {
		let days = 0;
		for (let baseMonth = 1; baseMonth < month + 1; baseMonth++) days += this.getSolarMonthDays(year, baseMonth);
		return days;
	}
	getSolarAbsDays(year, month, day) {
		return this.getSolarDaysBeforeBaseYear(year - 1) + this.getSolarDaysBeforeBaseMonth(year, month - 1) + day - LUNAR_CALENDAR_DATA.SOLAR_LUNAR_DAY_DIFF;
	}
	setSolarDateByLunarDate(lunarYear, lunarMonth, lunarDay, isIntercalation) {
		const absDays = this.getLunarAbsDays(lunarYear, lunarMonth, lunarDay, isIntercalation);
		const solarYear = absDays < this.getSolarAbsDays(lunarYear + 1, 1, 1) ? lunarYear : lunarYear + 1;
		let solarMonth = 0;
		let solarDay = 0;
		for (let month = 12; month > 0; month--) {
			const absDaysByMonth = this.getSolarAbsDays(solarYear, month, 1);
			if (absDays >= absDaysByMonth) {
				solarMonth = month;
				solarDay = absDays - absDaysByMonth + 1;
				break;
			}
		}
		this.solarCalendar = {
			year: solarYear,
			month: solarMonth,
			day: solarDay
		};
	}
	setLunarDateBySolarDate(solarYear, solarMonth, solarDay) {
		const absDays = this.getSolarAbsDays(solarYear, solarMonth, solarDay);
		const lunarYear = absDays >= this.getLunarAbsDays(solarYear, 1, 1, false) ? solarYear : solarYear - 1;
		let lunarMonth = 0;
		let lunarDay = 0;
		let isIntercalation = false;
		for (let month = 12; month > 0; month--) if (absDays >= this.getLunarAbsDays(lunarYear, month, 1, false)) {
			lunarMonth = month;
			if (this.getLunarIntercalationMonth(this.getLunarData(lunarYear)) === month) isIntercalation = absDays >= this.getLunarAbsDays(lunarYear, month, 1, true);
			lunarDay = absDays - this.getLunarAbsDays(lunarYear, lunarMonth, 1, isIntercalation) + 1;
			break;
		}
		this.lunarCalendar = {
			year: lunarYear,
			month: lunarMonth,
			day: lunarDay,
			intercalation: isIntercalation
		};
	}
	checkValidDate(isLunar, isIntercalation, year, month, day) {
		let isValid = false;
		if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day)) return false;
		const dateValue = year * 1e4 + month * 100 + day;
		if ((isLunar ? LUNAR_CALENDAR_DATA.KOREAN_LUNAR_MIN_VALUE : LUNAR_CALENDAR_DATA.KOREAN_SOLAR_MIN_VALUE) <= dateValue && (isLunar ? LUNAR_CALENDAR_DATA.KOREAN_LUNAR_MAX_VALUE : LUNAR_CALENDAR_DATA.KOREAN_SOLAR_MAX_VALUE) >= dateValue) {
			if (month > 0 && month < 13 && day > 0) {
				if (isLunar && isIntercalation && this.getLunarIntercalationMonth(this.getLunarData(year)) !== month) return false;
				const dayLimit = isLunar ? this.getLunarMonthDays(year, month, isIntercalation) : this.getSolarMonthDays(year, month);
				if (!isLunar && year === 1582 && month === 10 && day > 4 && day < 15) return false;
				if (day <= dayLimit) isValid = true;
			}
		}
		return isValid;
	}
	setLunarDate(lunarYear, lunarMonth, lunarDay, isIntercalation) {
		let isValid = false;
		if (this.checkValidDate(true, isIntercalation, lunarYear, lunarMonth, lunarDay)) {
			this.lunarCalendar = {
				year: lunarYear,
				month: lunarMonth,
				day: lunarDay,
				intercalation: isIntercalation && this.getLunarIntercalationMonth(this.getLunarData(lunarYear)) === lunarMonth
			};
			this.setSolarDateByLunarDate(lunarYear, lunarMonth, lunarDay, isIntercalation);
			isValid = true;
		}
		return isValid;
	}
	setSolarDate(solarYear, solarMonth, solarDay) {
		let isValid = false;
		if (this.checkValidDate(false, false, solarYear, solarMonth, solarDay)) {
			this.solarCalendar = {
				year: solarYear,
				month: solarMonth,
				day: solarDay
			};
			this.setLunarDateBySolarDate(solarYear, solarMonth, solarDay);
			isValid = true;
		}
		return isValid;
	}
	computeGapJa() {
		const lunar = this.lunarCalendar;
		const absDays = this.getLunarAbsDays(lunar.year, lunar.month, lunar.day, !!lunar.intercalation);
		if (absDays <= 0) return {
			cheongan: {
				year: 0,
				month: 0,
				day: 0
			},
			ganji: {
				year: 0,
				month: 0,
				day: 0
			}
		};
		const baseYear = LUNAR_CALENDAR_DATA.KOREAN_LUNAR_BASE_YEAR;
		const cheonganLen = LUNAR_CALENDAR_DATA.KOREAN_CHEONGAN.length;
		const ganjiLen = LUNAR_CALENDAR_DATA.KOREAN_GANJI.length;
		const monthCount = lunar.month + 12 * (lunar.year - baseYear);
		return {
			cheongan: {
				year: (lunar.year + GAPJA_OFFSET.YEAR_CHEONGAN - baseYear) % cheonganLen,
				month: (monthCount + GAPJA_OFFSET.MONTH_CHEONGAN) % cheonganLen,
				day: (absDays + GAPJA_OFFSET.DAY_CHEONGAN) % cheonganLen
			},
			ganji: {
				year: (lunar.year + GAPJA_OFFSET.YEAR_GANJI - baseYear) % ganjiLen,
				month: (monthCount + GAPJA_OFFSET.MONTH_GANJI) % ganjiLen,
				day: (absDays + GAPJA_OFFSET.DAY_GANJI) % ganjiLen
			}
		};
	}
	getGapJaIndex() {
		return this.computeGapJa();
	}
	getGapja(isChinese) {
		const inx = this.getGapJaIndex();
		const cheongan = !isChinese ? LUNAR_CALENDAR_DATA.KOREAN_CHEONGAN : LUNAR_CALENDAR_DATA.CHINESE_CHEONGAN;
		const ganji = !isChinese ? LUNAR_CALENDAR_DATA.KOREAN_GANJI : LUNAR_CALENDAR_DATA.CHINESE_GANJI;
		const unit = !isChinese ? LUNAR_CALENDAR_DATA.KOREAN_GAPJA_UNIT : LUNAR_CALENDAR_DATA.CHINESE_GAPJA_UNIT;
		const intercalationStr = !isChinese ? `${LUNAR_CALENDAR_DATA.INTERCALATION_STR[0]}${LUNAR_CALENDAR_DATA.KOREAN_GAPJA_UNIT[1]}` : `${LUNAR_CALENDAR_DATA.INTERCALATION_STR[1]}${LUNAR_CALENDAR_DATA.CHINESE_GAPJA_UNIT[1]}`;
		return {
			year: `${cheongan[inx.cheongan.year]}${ganji[inx.ganji.year]}${unit[0]}`,
			month: `${cheongan[inx.cheongan.month]}${ganji[inx.ganji.month]}${unit[1]}`,
			day: `${cheongan[inx.cheongan.day]}${ganji[inx.ganji.day]}${unit[2]}`,
			intercalation: this.lunarCalendar.intercalation ? intercalationStr : ""
		};
	}
	getKoreanGapja() {
		return this.getGapja();
	}
	getChineseGapja() {
		return this.getGapja(true);
	}
	getLunarCalendar() {
		return { ...this.lunarCalendar };
	}
	getSolarCalendar() {
		return { ...this.solarCalendar };
	}
};
//#endregion



return KoreanLunarCalendar;
})();

// Public administrative names/codes from MOIS, retrieved 2026-10-10.
// Source: https://jumin.mois.go.kr/ageStatMonth.do and its public region list.
// Legacy aliases are lookup conveniences, not historical boundary conversion.
const KOREA_REGIONS = [
  {
    "id": "1100000000",
    "name": "서울특별시",
    "label": "서울특별시",
    "code": "1100000000",
    "aliases": [],
    "districts": [
      {
        "id": "1111000000",
        "name": "종로구"
      },
      {
        "id": "1114000000",
        "name": "중구"
      },
      {
        "id": "1117000000",
        "name": "용산구"
      },
      {
        "id": "1120000000",
        "name": "성동구"
      },
      {
        "id": "1121500000",
        "name": "광진구"
      },
      {
        "id": "1123000000",
        "name": "동대문구"
      },
      {
        "id": "1126000000",
        "name": "중랑구"
      },
      {
        "id": "1129000000",
        "name": "성북구"
      },
      {
        "id": "1130500000",
        "name": "강북구"
      },
      {
        "id": "1132000000",
        "name": "도봉구"
      },
      {
        "id": "1135000000",
        "name": "노원구"
      },
      {
        "id": "1138000000",
        "name": "은평구"
      },
      {
        "id": "1141000000",
        "name": "서대문구"
      },
      {
        "id": "1144000000",
        "name": "마포구"
      },
      {
        "id": "1147000000",
        "name": "양천구"
      },
      {
        "id": "1150000000",
        "name": "강서구"
      },
      {
        "id": "1153000000",
        "name": "구로구"
      },
      {
        "id": "1154500000",
        "name": "금천구"
      },
      {
        "id": "1156000000",
        "name": "영등포구"
      },
      {
        "id": "1159000000",
        "name": "동작구"
      },
      {
        "id": "1162000000",
        "name": "관악구"
      },
      {
        "id": "1165000000",
        "name": "서초구"
      },
      {
        "id": "1168000000",
        "name": "강남구"
      },
      {
        "id": "1171000000",
        "name": "송파구"
      },
      {
        "id": "1174000000",
        "name": "강동구"
      }
    ]
  },
  {
    "id": "1200000000",
    "name": "전남광주통합특별시",
    "label": "전남광주통합특별시 (광주·전남)",
    "code": "1200000000",
    "aliases": [],
    "districts": [
      {
        "id": "1211000000",
        "name": "목포시"
      },
      {
        "id": "1213000000",
        "name": "여수시"
      },
      {
        "id": "1215000000",
        "name": "순천시"
      },
      {
        "id": "1217000000",
        "name": "나주시"
      },
      {
        "id": "1219000000",
        "name": "광양시"
      },
      {
        "id": "1221000000",
        "name": "동구"
      },
      {
        "id": "1224000000",
        "name": "서구"
      },
      {
        "id": "1227000000",
        "name": "남구"
      },
      {
        "id": "1230000000",
        "name": "북구"
      },
      {
        "id": "1233000000",
        "name": "광산구"
      },
      {
        "id": "1271000000",
        "name": "담양군"
      },
      {
        "id": "1272000000",
        "name": "곡성군"
      },
      {
        "id": "1273000000",
        "name": "구례군"
      },
      {
        "id": "1274000000",
        "name": "고흥군"
      },
      {
        "id": "1275000000",
        "name": "보성군"
      },
      {
        "id": "1276000000",
        "name": "화순군"
      },
      {
        "id": "1277000000",
        "name": "장흥군"
      },
      {
        "id": "1278000000",
        "name": "강진군"
      },
      {
        "id": "1279000000",
        "name": "해남군"
      },
      {
        "id": "1280000000",
        "name": "영암군"
      },
      {
        "id": "1281000000",
        "name": "무안군"
      },
      {
        "id": "1282000000",
        "name": "함평군"
      },
      {
        "id": "1283000000",
        "name": "영광군"
      },
      {
        "id": "1284000000",
        "name": "장성군"
      },
      {
        "id": "1285000000",
        "name": "완도군"
      },
      {
        "id": "1286000000",
        "name": "진도군"
      },
      {
        "id": "1287000000",
        "name": "신안군"
      }
    ]
  },
  {
    "id": "2600000000",
    "name": "부산광역시",
    "label": "부산광역시",
    "code": "2600000000",
    "aliases": [],
    "districts": [
      {
        "id": "2611000000",
        "name": "중구"
      },
      {
        "id": "2614000000",
        "name": "서구"
      },
      {
        "id": "2617000000",
        "name": "동구"
      },
      {
        "id": "2620000000",
        "name": "영도구"
      },
      {
        "id": "2623000000",
        "name": "부산진구"
      },
      {
        "id": "2626000000",
        "name": "동래구"
      },
      {
        "id": "2629000000",
        "name": "남구"
      },
      {
        "id": "2632000000",
        "name": "북구"
      },
      {
        "id": "2635000000",
        "name": "해운대구"
      },
      {
        "id": "2638000000",
        "name": "사하구"
      },
      {
        "id": "2641000000",
        "name": "금정구"
      },
      {
        "id": "2644000000",
        "name": "강서구"
      },
      {
        "id": "2647000000",
        "name": "연제구"
      },
      {
        "id": "2650000000",
        "name": "수영구"
      },
      {
        "id": "2653000000",
        "name": "사상구"
      },
      {
        "id": "2671000000",
        "name": "기장군"
      }
    ]
  },
  {
    "id": "2700000000",
    "name": "대구광역시",
    "label": "대구광역시",
    "code": "2700000000",
    "aliases": [],
    "districts": [
      {
        "id": "2711000000",
        "name": "중구"
      },
      {
        "id": "2714000000",
        "name": "동구"
      },
      {
        "id": "2717000000",
        "name": "서구"
      },
      {
        "id": "2720000000",
        "name": "남구"
      },
      {
        "id": "2723000000",
        "name": "북구"
      },
      {
        "id": "2726000000",
        "name": "수성구"
      },
      {
        "id": "2729000000",
        "name": "달서구"
      },
      {
        "id": "2771000000",
        "name": "달성군"
      },
      {
        "id": "2772000000",
        "name": "군위군"
      }
    ]
  },
  {
    "id": "2800000000",
    "name": "인천광역시",
    "label": "인천광역시",
    "code": "2800000000",
    "aliases": [],
    "districts": [
      {
        "id": "2812500000",
        "name": "제물포구"
      },
      {
        "id": "2815500000",
        "name": "영종구"
      },
      {
        "id": "2817700000",
        "name": "미추홀구"
      },
      {
        "id": "2818500000",
        "name": "연수구"
      },
      {
        "id": "2820000000",
        "name": "남동구"
      },
      {
        "id": "2823700000",
        "name": "부평구"
      },
      {
        "id": "2824500000",
        "name": "계양구"
      },
      {
        "id": "2827500000",
        "name": "서해구"
      },
      {
        "id": "2829000000",
        "name": "검단구"
      },
      {
        "id": "2871000000",
        "name": "강화군"
      },
      {
        "id": "2872000000",
        "name": "옹진군"
      }
    ]
  },
  {
    "id": "3000000000",
    "name": "대전광역시",
    "label": "대전광역시",
    "code": "3000000000",
    "aliases": [],
    "districts": [
      {
        "id": "3011000000",
        "name": "동구"
      },
      {
        "id": "3014000000",
        "name": "중구"
      },
      {
        "id": "3017000000",
        "name": "서구"
      },
      {
        "id": "3020000000",
        "name": "유성구"
      },
      {
        "id": "3023000000",
        "name": "대덕구"
      }
    ]
  },
  {
    "id": "3100000000",
    "name": "울산광역시",
    "label": "울산광역시",
    "code": "3100000000",
    "aliases": [],
    "districts": [
      {
        "id": "3111000000",
        "name": "중구"
      },
      {
        "id": "3114000000",
        "name": "남구"
      },
      {
        "id": "3117000000",
        "name": "동구"
      },
      {
        "id": "3120000000",
        "name": "북구"
      },
      {
        "id": "3171000000",
        "name": "울주군"
      }
    ]
  },
  {
    "id": "3600000000",
    "name": "세종특별자치시",
    "label": "세종특별자치시",
    "code": "3600000000",
    "aliases": [],
    "districts": [
      {
        "id": "3611000000",
        "name": "세종특별자치시"
      }
    ]
  },
  {
    "id": "4100000000",
    "name": "경기도",
    "label": "경기도",
    "code": "4100000000",
    "aliases": [],
    "districts": [
      {
        "id": "4111000000",
        "name": "수원시"
      },
      {
        "id": "4113000000",
        "name": "성남시"
      },
      {
        "id": "4115000000",
        "name": "의정부시"
      },
      {
        "id": "4117000000",
        "name": "안양시"
      },
      {
        "id": "4119000000",
        "name": "부천시"
      },
      {
        "id": "4121000000",
        "name": "광명시"
      },
      {
        "id": "4122000000",
        "name": "평택시"
      },
      {
        "id": "4125000000",
        "name": "동두천시"
      },
      {
        "id": "4127000000",
        "name": "안산시"
      },
      {
        "id": "4128000000",
        "name": "고양시"
      },
      {
        "id": "4129000000",
        "name": "과천시"
      },
      {
        "id": "4131000000",
        "name": "구리시"
      },
      {
        "id": "4136000000",
        "name": "남양주시"
      },
      {
        "id": "4137000000",
        "name": "오산시"
      },
      {
        "id": "4139000000",
        "name": "시흥시"
      },
      {
        "id": "4141000000",
        "name": "군포시"
      },
      {
        "id": "4143000000",
        "name": "의왕시"
      },
      {
        "id": "4145000000",
        "name": "하남시"
      },
      {
        "id": "4146000000",
        "name": "용인시"
      },
      {
        "id": "4148000000",
        "name": "파주시"
      },
      {
        "id": "4150000000",
        "name": "이천시"
      },
      {
        "id": "4155000000",
        "name": "안성시"
      },
      {
        "id": "4157000000",
        "name": "김포시"
      },
      {
        "id": "4159000000",
        "name": "화성시"
      },
      {
        "id": "4161000000",
        "name": "광주시"
      },
      {
        "id": "4163000000",
        "name": "양주시"
      },
      {
        "id": "4165000000",
        "name": "포천시"
      },
      {
        "id": "4167000000",
        "name": "여주시"
      },
      {
        "id": "4180000000",
        "name": "연천군"
      },
      {
        "id": "4182000000",
        "name": "가평군"
      },
      {
        "id": "4183000000",
        "name": "양평군"
      }
    ]
  },
  {
    "id": "5100000000",
    "name": "강원특별자치도",
    "label": "강원특별자치도 (강원도)",
    "code": "5100000000",
    "aliases": [
      "강원도",
      "강원"
    ],
    "districts": [
      {
        "id": "5111000000",
        "name": "춘천시"
      },
      {
        "id": "5113000000",
        "name": "원주시"
      },
      {
        "id": "5115000000",
        "name": "강릉시"
      },
      {
        "id": "5117000000",
        "name": "동해시"
      },
      {
        "id": "5119000000",
        "name": "태백시"
      },
      {
        "id": "5121000000",
        "name": "속초시"
      },
      {
        "id": "5123000000",
        "name": "삼척시"
      },
      {
        "id": "5172000000",
        "name": "홍천군"
      },
      {
        "id": "5173000000",
        "name": "횡성군"
      },
      {
        "id": "5175000000",
        "name": "영월군"
      },
      {
        "id": "5176000000",
        "name": "평창군"
      },
      {
        "id": "5177000000",
        "name": "정선군"
      },
      {
        "id": "5178000000",
        "name": "철원군"
      },
      {
        "id": "5179000000",
        "name": "화천군"
      },
      {
        "id": "5180000000",
        "name": "양구군"
      },
      {
        "id": "5181000000",
        "name": "인제군"
      },
      {
        "id": "5182000000",
        "name": "고성군"
      },
      {
        "id": "5183000000",
        "name": "양양군"
      }
    ]
  },
  {
    "id": "4300000000",
    "name": "충청북도",
    "label": "충청북도",
    "code": "4300000000",
    "aliases": [],
    "districts": [
      {
        "id": "4311000000",
        "name": "청주시"
      },
      {
        "id": "4313000000",
        "name": "충주시"
      },
      {
        "id": "4315000000",
        "name": "제천시"
      },
      {
        "id": "4372000000",
        "name": "보은군"
      },
      {
        "id": "4373000000",
        "name": "옥천군"
      },
      {
        "id": "4374000000",
        "name": "영동군"
      },
      {
        "id": "4374500000",
        "name": "증평군"
      },
      {
        "id": "4375000000",
        "name": "진천군"
      },
      {
        "id": "4376000000",
        "name": "괴산군"
      },
      {
        "id": "4377000000",
        "name": "음성군"
      },
      {
        "id": "4380000000",
        "name": "단양군"
      }
    ]
  },
  {
    "id": "4400000000",
    "name": "충청남도",
    "label": "충청남도",
    "code": "4400000000",
    "aliases": [],
    "districts": [
      {
        "id": "4413000000",
        "name": "천안시"
      },
      {
        "id": "4415000000",
        "name": "공주시"
      },
      {
        "id": "4418000000",
        "name": "보령시"
      },
      {
        "id": "4420000000",
        "name": "아산시"
      },
      {
        "id": "4421000000",
        "name": "서산시"
      },
      {
        "id": "4423000000",
        "name": "논산시"
      },
      {
        "id": "4425000000",
        "name": "계룡시"
      },
      {
        "id": "4427000000",
        "name": "당진시"
      },
      {
        "id": "4471000000",
        "name": "금산군"
      },
      {
        "id": "4476000000",
        "name": "부여군"
      },
      {
        "id": "4477000000",
        "name": "서천군"
      },
      {
        "id": "4479000000",
        "name": "청양군"
      },
      {
        "id": "4480000000",
        "name": "홍성군"
      },
      {
        "id": "4481000000",
        "name": "예산군"
      },
      {
        "id": "4482500000",
        "name": "태안군"
      }
    ]
  },
  {
    "id": "5200000000",
    "name": "전북특별자치도",
    "label": "전북특별자치도 (전라북도)",
    "code": "5200000000",
    "aliases": [
      "전라북도",
      "전북"
    ],
    "districts": [
      {
        "id": "5211000000",
        "name": "전주시"
      },
      {
        "id": "5213000000",
        "name": "군산시"
      },
      {
        "id": "5214000000",
        "name": "익산시"
      },
      {
        "id": "5218000000",
        "name": "정읍시"
      },
      {
        "id": "5219000000",
        "name": "남원시"
      },
      {
        "id": "5221000000",
        "name": "김제시"
      },
      {
        "id": "5271000000",
        "name": "완주군"
      },
      {
        "id": "5272000000",
        "name": "진안군"
      },
      {
        "id": "5273000000",
        "name": "무주군"
      },
      {
        "id": "5274000000",
        "name": "장수군"
      },
      {
        "id": "5275000000",
        "name": "임실군"
      },
      {
        "id": "5277000000",
        "name": "순창군"
      },
      {
        "id": "5279000000",
        "name": "고창군"
      },
      {
        "id": "5280000000",
        "name": "부안군"
      }
    ]
  },
  {
    "id": "4700000000",
    "name": "경상북도",
    "label": "경상북도",
    "code": "4700000000",
    "aliases": [],
    "districts": [
      {
        "id": "4711000000",
        "name": "포항시"
      },
      {
        "id": "4713000000",
        "name": "경주시"
      },
      {
        "id": "4715000000",
        "name": "김천시"
      },
      {
        "id": "4717000000",
        "name": "안동시"
      },
      {
        "id": "4719000000",
        "name": "구미시"
      },
      {
        "id": "4721000000",
        "name": "영주시"
      },
      {
        "id": "4723000000",
        "name": "영천시"
      },
      {
        "id": "4725000000",
        "name": "상주시"
      },
      {
        "id": "4728000000",
        "name": "문경시"
      },
      {
        "id": "4729000000",
        "name": "경산시"
      },
      {
        "id": "4773000000",
        "name": "의성군"
      },
      {
        "id": "4775000000",
        "name": "청송군"
      },
      {
        "id": "4776000000",
        "name": "영양군"
      },
      {
        "id": "4777000000",
        "name": "영덕군"
      },
      {
        "id": "4782000000",
        "name": "청도군"
      },
      {
        "id": "4783000000",
        "name": "고령군"
      },
      {
        "id": "4784000000",
        "name": "성주군"
      },
      {
        "id": "4785000000",
        "name": "칠곡군"
      },
      {
        "id": "4790000000",
        "name": "예천군"
      },
      {
        "id": "4792000000",
        "name": "봉화군"
      },
      {
        "id": "4793000000",
        "name": "울진군"
      },
      {
        "id": "4794000000",
        "name": "울릉군"
      }
    ]
  },
  {
    "id": "4800000000",
    "name": "경상남도",
    "label": "경상남도",
    "code": "4800000000",
    "aliases": [],
    "districts": [
      {
        "id": "4812000000",
        "name": "창원시"
      },
      {
        "id": "4817000000",
        "name": "진주시"
      },
      {
        "id": "4822000000",
        "name": "통영시"
      },
      {
        "id": "4824000000",
        "name": "사천시"
      },
      {
        "id": "4825000000",
        "name": "김해시"
      },
      {
        "id": "4827000000",
        "name": "밀양시"
      },
      {
        "id": "4831000000",
        "name": "거제시"
      },
      {
        "id": "4833000000",
        "name": "양산시"
      },
      {
        "id": "4872000000",
        "name": "의령군"
      },
      {
        "id": "4873000000",
        "name": "함안군"
      },
      {
        "id": "4874000000",
        "name": "창녕군"
      },
      {
        "id": "4882000000",
        "name": "고성군"
      },
      {
        "id": "4884000000",
        "name": "남해군"
      },
      {
        "id": "4885000000",
        "name": "하동군"
      },
      {
        "id": "4886000000",
        "name": "산청군"
      },
      {
        "id": "4887000000",
        "name": "함양군"
      },
      {
        "id": "4888000000",
        "name": "거창군"
      },
      {
        "id": "4889000000",
        "name": "합천군"
      }
    ]
  },
  {
    "id": "5000000000",
    "name": "제주특별자치도",
    "label": "제주특별자치도",
    "code": "5000000000",
    "aliases": [],
    "districts": [
      {
        "id": "5011000000",
        "name": "제주시"
      },
      {
        "id": "5013000000",
        "name": "서귀포시"
      }
    ]
  },
  {
    "id": "legacy-gwangju",
    "code": "1200000000",
    "name": "광주광역시",
    "label": "광주광역시 (옛 명칭)",
    "aliases": [
      "광주"
    ],
    "legacy": true,
    "districts": [
      {
        "id": "1221000000",
        "name": "동구"
      },
      {
        "id": "1224000000",
        "name": "서구"
      },
      {
        "id": "1227000000",
        "name": "남구"
      },
      {
        "id": "1230000000",
        "name": "북구"
      },
      {
        "id": "1233000000",
        "name": "광산구"
      }
    ]
  },
  {
    "id": "legacy-jeonnam",
    "code": "1200000000",
    "name": "전라남도",
    "label": "전라남도 (옛 명칭)",
    "aliases": [
      "전남"
    ],
    "legacy": true,
    "districts": [
      {
        "id": "1211000000",
        "name": "목포시"
      },
      {
        "id": "1213000000",
        "name": "여수시"
      },
      {
        "id": "1215000000",
        "name": "순천시"
      },
      {
        "id": "1217000000",
        "name": "나주시"
      },
      {
        "id": "1219000000",
        "name": "광양시"
      },
      {
        "id": "1271000000",
        "name": "담양군"
      },
      {
        "id": "1272000000",
        "name": "곡성군"
      },
      {
        "id": "1273000000",
        "name": "구례군"
      },
      {
        "id": "1274000000",
        "name": "고흥군"
      },
      {
        "id": "1275000000",
        "name": "보성군"
      },
      {
        "id": "1276000000",
        "name": "화순군"
      },
      {
        "id": "1277000000",
        "name": "장흥군"
      },
      {
        "id": "1278000000",
        "name": "강진군"
      },
      {
        "id": "1279000000",
        "name": "해남군"
      },
      {
        "id": "1280000000",
        "name": "영암군"
      },
      {
        "id": "1281000000",
        "name": "무안군"
      },
      {
        "id": "1282000000",
        "name": "함평군"
      },
      {
        "id": "1283000000",
        "name": "영광군"
      },
      {
        "id": "1284000000",
        "name": "장성군"
      },
      {
        "id": "1285000000",
        "name": "완도군"
      },
      {
        "id": "1286000000",
        "name": "진도군"
      },
      {
        "id": "1287000000",
        "name": "신안군"
      }
    ]
  }
];
const KOREA_REGIONS_VERSION = 'MOIS-2026-10-10';


// Birth information is local civil time, never the browser's timezone.
// Keep uncertainty explicit; the preview does not calculate a saju chart.
const birthEscape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const birthPad=n=>String(n).padStart(2,'0');
const BIRTH_MIN_YEAR=1940,BIRTH_MAX_YEAR=2026;
const birthISO=v=>`${v.year}-${birthPad(v.month)}-${birthPad(v.day)}`;
const birthCountries=[['KR','대한민국']];
const birthMonthCache=new Map();
function birthToday(){const parts=Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date()).map(p=>[p.type,p.value]));return `${parts.year}-${parts.month}-${parts.day}`}
function lunarMonthInfo(year,month,leap=false){
 const key=`${year}/${month}/${leap}`;
 if(birthMonthCache.has(key))return birthMonthCache.get(key);
 if(!Number.isInteger(year)||year<BIRTH_MIN_YEAR||year>BIRTH_MAX_YEAR||!Number.isInteger(month)||month<1||month>12)return {valid:false,days:0,hasLeap:false};
 const c=new KoreanLunarCalendar(),hasLeap=c.setLunarDate(year,month,1,true);
 const valid=c.setLunarDate(year,month,1,leap);
 const info={valid,hasLeap,days:valid?(c.setLunarDate(year,month,30,leap)?30:29):0};
 birthMonthCache.set(key,info);return info;
}
function validateBirthDate(value,today=birthToday()){
 const date=String(value.birth||''),calendar=value.calendar||'solar';
 if(calendar==='unknown')return {valid:false,code:'DATE_UNCONFIRMED',message:'양력인지 음력인지 확인한 뒤 진행할 수 있어요.'};
 if(calendar==='lunar'&&(value.leapStatus==='unknown'||value.leap===null))return {valid:false,code:'DATE_UNCONFIRMED',message:'평달인지 윤달인지 확인한 뒤 진행할 수 있어요.'};
 if(calendar==='lunar'&&typeof value.leap!=='boolean')return {valid:false,code:'DATE_UNCONFIRMED',message:'평달 또는 윤달 여부를 선택해주세요.'};
 if(!/^\d{4}-\d{2}-\d{2}$/.test(date))return {valid:false,message:'생년월일을 모두 입력해주세요.'};
 const [year,month,day]=date.split('-').map(Number);
 if(year<BIRTH_MIN_YEAR||year>BIRTH_MAX_YEAR)return {valid:false,message:`${BIRTH_MIN_YEAR}년부터 ${BIRTH_MAX_YEAR}년까지 선택할 수 있어요.`};
 if(!['solar','lunar'].includes(calendar))return {valid:false,message:'양력 또는 음력을 선택해주세요.'};
 const c=new KoreanLunarCalendar();
 if(calendar==='lunar'){
  const info=lunarMonthInfo(year,month,!!value.leap);
  if(value.leap&&!info.hasLeap)return {valid:false,message:`${year}년 음력 ${month}월에는 윤달이 없어요. 월이나 윤달 선택을 확인해주세요.`};
  if(!info.valid||day<1||day>info.days)return {valid:false,message:info.days?`선택한 음력 월은 ${info.days}일까지 있어요.`:'음력 월과 일을 확인해주세요.'};
  if(!c.setLunarDate(year,month,day,!!value.leap))return {valid:false,message:'존재하지 않거나 지원 범위를 벗어난 음력 날짜예요.'};
  const back=c.getLunarCalendar();
  if(back.year!==year||back.month!==month||back.day!==day||!!back.intercalation!==!!value.leap)return {valid:false,message:'음력 날짜와 윤달 여부를 확인해주세요.'};
 }else if(!c.setSolarDate(year,month,day))return {valid:false,message:'존재하지 않는 양력 날짜예요.'};
 const solarDate=birthISO(c.getSolarCalendar());
 if(solarDate>today)return {valid:false,message:'미래의 날짜는 생일로 입력할 수 없어요.'};
 return {valid:true,solarDate,message:calendar==='lunar'?`양력 ${solarDate.replaceAll('-','.')}에 해당해요.`:''};
}
function birthPrecision(value){return value.timeAccuracy|| (value.unknown?'unknown':'exact')}
function birthTimeMinutes(time){return typeof time==='string'&&/^([01]\d|2[0-3]):[0-5]\d$/.test(time)?Number(time.slice(0,2))*60+Number(time.slice(3)):null}
function birthRangeError(value){
 const accuracy=birthPrecision(value);
 if(accuracy==='unknown')return '';
 if(accuracy==='exact')return birthTimeMinutes(value.time)!==null?'':'태어난 시각을 입력해주세요.';
 if(accuracy!=='approximate')return '시간의 정확도를 선택해주세요.';
 const range=value.timeRange||{},start=birthTimeMinutes(range.start),end=birthTimeMinutes(range.end);
 if(![0,1].includes(range.endDayOffset))return '시간 범위가 당일인지 다음 날인지 확인해주세요.';
 if(start===null||end===null)return '기억나는 시간 범위의 시작과 끝을 입력해주세요.';
 const duration=end+(range.endDayOffset===1?1440:0)-start;
 if(duration<=0)return '끝 시간을 시작보다 뒤로 선택해주세요. 자정을 넘으면 다음 날에 끝남을 선택해주세요.';
 if(duration>1440)return '시간 범위는 24시간 이내로 입력해주세요.';
 return '';
}
function resolveBirthRegion(place={}){
 const selected=KOREA_REGIONS.find(r=>r.id===place.regionChoice);
 if(selected)return {region:selected,district:selected.districts.find(d=>d.id===place.districtCode)||null,manual:place.inputMode==='manual',text:place.inputMode==='manual'?place.city||'':''};
 const raw=String(place.city||'').trim();
 for(const region of KOREA_REGIONS){
  for(const label of [region.name,...region.aliases])if(raw===label||raw.startsWith(label+' ')){
   const remainder=raw.slice(label.length).trim(),district=region.districts.find(d=>remainder===d.name||remainder.startsWith(d.name+' '));
   return {region,district:district||null,manual:!!remainder&&!district,text:!district?remainder:''};
  }
 }
 return {region:null,district:null,manual:false,text:raw};
}
function birthPlaceReferenceValid(place,today=birthToday()){
 const era=place?.referenceEra??'unknown',date=place?.referenceDate;
 if(!['current','at_birth','unknown'].includes(era))return false;
 if(era!=='current')return date===undefined||date===null;
 if(!/^\d{4}-\d{2}-\d{2}$/.test(date??'')||date>today)return false;
 const parsed=new Date(date+'T00:00:00Z');return Number.isFinite(+parsed)&&parsed.toISOString().slice(0,10)===date;
}
function birthPlaceValid(place){
 if(!birthPlaceReferenceValid(place))return false;
 if(!place||place.countryCode!=='KR')return false;if(place.status==='unknown')return true;
 const countryOK=typeof place.countryName==='string'&&!!place.countryName.trim()&&place.countryName.length<=80&&(!place.countryCode||birthCountries.some(([code])=>code===place.countryCode&&code!=='OTHER'));
 if(!countryOK)return false;if(place.status==='country-only')return true;
 if(place.countryCode==='KR'){
  const region=KOREA_REGIONS.find(r=>r.id===place.regionChoice);
  if(!region||place.regionCode!==region.code)return false;
  if(place.status==='region-only')return true;
  if(place.status!=='known')return false;
  if(place.inputMode==='manual')return typeof place.city==='string'&&!!place.city.trim()&&place.city.length<=100&&place.districtCode===null;
  return place.inputMode==='list'&&region.districts.some(d=>d.id===place.districtCode&&d.name===place.city);
 }
 return place.status==='known'&&typeof place.city==='string'&&!!place.city.trim()&&place.city.length<=100;
}
function birthReadableTime(time){
 if(birthTimeMinutes(time)===null)return '시각 미입력';
 const hour=Number(time.slice(0,2));return (hour<12?'오전 ':'오후 ')+birthPad(hour%12)+'시 '+time.slice(3)+'분';
}
function birthNextDate(iso){const d=new Date(iso+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+1);return d.toISOString().slice(0,10)}
function birthAnalysisInput(value){
 const date=validateBirthDate(value),accuracy=birthPrecision(value),place=value.birthPlace||{status:'unprovided'};
 const ready=date.valid&&!birthRangeError(value)&&birthPlaceValid(place);
 let interval=null;
 if(date.valid&&accuracy==='approximate'&&!birthRangeError(value)){
  const range=value.timeRange;
  interval={startLocal:`${date.solarDate}T${range.start}`,endLocal:`${range.endDayOffset===1?birthNextDate(date.solarDate):date.solarDate}T${range.end}`,endpoints:'inclusive',timezone:null};
 }
 if(date.valid&&accuracy==='unknown')interval={startLocal:`${date.solarDate}T00:00`,endLocal:`${birthNextDate(date.solarDate)}T00:00`,endpoints:'start_inclusive_end_exclusive',timezone:null};
 return {
  version:2,status:ready?'awaiting_analysis_service':'incomplete',solarDate:date.valid?date.solarDate:null,
  calendarStandard:value.calendar==='lunar'?'korean-lunar': 'gregorian',
  localTime:accuracy==='exact'&&birthTimeMinutes(value.time)!==null?value.time:null,
  timeAccuracy:accuracy,timeInterval:interval,
  locationPolicy:place.status==='known'?'resolve_city_and_historical_timezone':'compare_possible_korean_locations_then_review',
  locationReference:{era:place.referenceEra??'unknown',date:place.referenceDate??null,eraAssumed:false},
  timezone:null,coordinates:null,
  timePolicy:accuracy==='exact'?'use_exact_local_time_and_check_boundaries':'compare_entire_interval',
  differingResultsPolicy:accuracy!=='exact'?'show_common_and_separate_variants':null,
  compareAt:['time_pillar_boundaries','adopted_day_boundary','local_midnight','solar_term_boundaries','historical_timezone_transitions'],
  // Never invent noon, an interval midpoint, Seoul, or a UTC offset.
  assumeMissingLocation:false,assumeMissingTime:false
 };
}
function personValid(value={}){
 return !!(typeof value.name==='string'&&value.name.trim()&&value.name.length<=30&&['male','female'].includes(value.sex)&&validateBirthDate(value).valid&&birthPlaceValid(value.birthPlace)&&!birthRangeError(value));
}

const PRODUCTS=[
  {
    "id": "lifetime",
    "name": "금월선녀의 평생사주",
    "short": "평생사주",
    "guide": "금월선녀",
    "category": "인생총운",
    "color": "#d8bb78",
    "tone": "forest",
    "symbol": "一生",
    "line": "지나온 나를 이해하고\n앞으로의 길을 만나다",
    "price": 49800,
    "original": 110000,
    "steps": 11
  },
  {
    "id": "romance",
    "name": "금월선녀의 연애사주",
    "short": "연애사주",
    "guide": "금월선녀",
    "category": "연애",
    "color": "#e0b0ae",
    "tone": "violet",
    "symbol": "戀",
    "line": "다음 사랑은\n어떤 모습으로 올까요",
    "price": 29800,
    "original": 55000,
    "steps": 9
  },
  {
    "id": "reunion",
    "name": "금월선녀의 재회사주",
    "short": "재회사주",
    "guide": "금월선녀",
    "category": "재회",
    "color": "#a6b9d9",
    "tone": "moon",
    "symbol": "再會",
    "line": "끝나지 않은 마음\n다시 이어질 수 있을까",
    "price": 29800,
    "original": 55000,
    "steps": 14
  },
  {
    "id": "intimate",
    "name": "금월선녀의 깊은 궁합",
    "short": "깊은 궁합",
    "guide": "금월선녀",
    "category": "연애",
    "color": "#d5a090",
    "tone": "rose",
    "symbol": "緣",
    "line": "말하지 못한 마음까지\n우리, 얼마나 닮았을까",
    "price": 29800,
    "original": 55000,
    "steps": 13
  },
  {
    "id": "wealth",
    "name": "금월선녀의 재물운",
    "short": "재물운",
    "guide": "금월선녀",
    "category": "금전",
    "color": "#d8bb78",
    "tone": "gold",
    "symbol": "財",
    "line": "내 삶의 결실은\n언제 익어갈까요",
    "price": 29800,
    "original": 55000,
    "steps": 8
  },
  {
    "id": "career",
    "name": "금월선녀의 직업·이직운",
    "short": "직업·이직운",
    "guide": "금월선녀",
    "category": "금전",
    "color": "#d8bb78",
    "tone": "gold",
    "symbol": "業",
    "line": "나에게 맞는 일\n움직여야 할 순간",
    "price": 29800,
    "original": 55000,
    "steps": 10
  },
  {
    "id": "business",
    "name": "금월선녀의 사업운",
    "short": "사업운",
    "guide": "금월선녀",
    "category": "금전",
    "color": "#d8bb78",
    "tone": "gold",
    "symbol": "商",
    "line": "내가 키우는 일\n사업의 다음 장을 읽다",
    "price": 29800,
    "original": 55000,
    "steps": 10
  },
  {
    "id": "health",
    "name": "금월선녀의 건강운",
    "short": "건강운",
    "guide": "금월선녀",
    "category": "건강",
    "color": "#9dc4b1",
    "tone": "teal",
    "symbol": "安",
    "line": "나의 몸과 마음\n돌봄의 리듬을 찾다",
    "price": 29800,
    "original": 55000,
    "steps": 10
  }
];

const scene=(id,title,text,cta='계속 이야기 듣기')=>({id,type:'scene',title,text,cta});
const intro=(title,text)=>({...scene('intro',title,text,'이야기 시작하기'),intro:true});
const info={id:'info',type:'info',who:'self',title:'당신의 이야기를 알려주세요'};
const partner={id:'partner',type:'info',who:'partner',title:'그 사람의 이야기도 들려주세요'};
const choice=(id,title,options,required=false)=>({id,type:'choice',title,options,required});
const question={id:'question',type:'question',title:'가장 궁금한 이야기가 있나요?',text:'지금의 상황이나 마음에 남은 질문을 편하게 들려주세요. 적지 않고 다음으로 가셔도 괜찮아요.'};
const sales={id:'sales',type:'sales'}; const checkout={id:'checkout',type:'checkout'};
const FLOWS={
lifetime:[intro('당신의 다음 장을\n펼쳐볼까요','오래 품어온 질문 하나, 이곳에 내려놓으세요.'),scene('welcome','기다리고 있었어요','지금까지 걸어온 길에도, 앞으로의 길에도 당신만의 흐름이 있어요.'),scene('grove','사람마다\n자라는 속도가 달라요','어떤 나무는 먼저 꽃을 피우고, 어떤 나무는 오래 뿌리를 내려요.'),scene('invite','이제 당신의\n이야기를 들을게요','나를 이해하는 일부터 함께 시작해요.','내 이야기 들려주기'),info,choice('occupation','요즘 어떤 일상을 보내고 있나요?',['직장에 다니고 있어요','사업을 하고 있어요','프리랜서로 일해요','공부하고 있어요','잠시 쉬고 있어요']),choice('relationship','지금, 연애와 결혼은 어떤 상태인가요?',['지금은 혼자예요','연애하고 있어요','결혼했어요','이혼하거나 사별했어요']),scene('omen','반복되는 고민에는\n이유가 있을까요','일, 관계, 선택 앞에서 자주 멈추게 되는 지점을 함께 살펴봐요.'),question,scene('ready','당신에게 필요한\n이야기를 모았어요','타고난 성향부터 앞으로의 선택까지, 차례로 펼쳐보세요.','내 리포트 살펴보기'),sales,checkout],
romance:[intro('다음 사랑은\n어떤 모습일까요','설레는 만남도, 자꾸 어긋나는 마음도. 오늘은 함께 이야기해요.'),scene('meet','어서 와요,\n사랑 이야기를 해볼까요','누군가를 좋아할 때의 당신은 어떤 사람인가요?'),scene('tease','마음이 움직이는\n순간이 궁금해요','잘하고 싶은 마음과 실제 표현은 가끔 다른 방향으로 가기도 하죠.','내 연애 이야기 시작하기'),info,choice('status','지금, 당신의 마음은 어디에 있나요?',['썸을 타고 있어요','연애 중이에요','지금은 솔로예요','최근에 헤어졌어요','오랫동안 혼자였어요'],true),choice('experience','지금까지 연애 경험은 얼마나 있나요?',['아직 없어요','1~2번','3~5번','6번 이상','정확히 세기 어려워요'],true),scene('ready','당신의 사랑에\n다음 장이 열린다면','반복되는 관계의 모습과 새로운 만남에 대해 차근차근 살펴봐요.','연애 리포트 살펴보기'),sales,checkout],
reunion:[intro('끝난 이야기에도\n남은 마음이 있나요','쉽게 놓이지 않는 이름, 오늘은 그 이야기를 들려주세요.'),scene('broom','조용한 곳으로\n잠시 함께 가요','마음을 정리할 수 있는 작은 틈이 필요할 때가 있어요.'),scene('flight','멀리서 보면\n다르게 보일 때가 있죠','가까이 있을 때 보지 못한 두 사람의 마음을 돌아봐요.'),scene('meet','반가워요,\n금월선녀예요','연락할까, 기다릴까. 그 사이에서 오래 망설였나요?'),scene('invite','서두르지 않아도\n괜찮아요','먼저 당신부터 알아갈게요.','내 정보 알려주기'),info,scene('ex','그 사람은\n어떤 사람이었나요','서로의 다름과 함께했던 시간을 같이 살펴보려 해요.'),partner,scene('ask','몇 가지 이야기를\n더 들려주세요','관계의 현재 모습을 이해하는 데 도움이 돼요.'),choice('breakup','헤어진 지 얼마나 되었나요?',['3개월 이내예요','3~6개월 정도예요','6개월~1년 정도예요','1년 이상 지났어요','아직 헤어지지 않았어요']),{...question,title:'두 사람에게 어떤 일이 있었나요?'},scene('ready','돌아봄의 끝에서\n나의 선택을 찾도록','관계의 패턴과 대화의 방향을 차분히 읽어보세요.','재회 리포트 살펴보기'),sales,checkout],
intimate:[intro('말하지 않은 마음도\n이야기가 됩니다','두 사람 사이에 흐르는 온도를 천천히 들여다봐요.'),scene('meet','두 사람의 이야기를\n기다렸어요','함께 있을 때 가장 편안한 순간은 언제인가요?'),scene('invite','이쪽으로\n들어오세요','서로에 대해 미처 묻지 못한 것부터 이야기해요.'),scene('bond','가까울수록\n다를 수 있어요','좋아하는 표현과 필요한 거리가 서로 다를 수 있죠.'),choice('status','지금 두 사람은 어떤 관계인가요?',['연애 중이에요','혼자 좋아하고 있어요','서로 알아가는 중이에요','결혼한 사이예요','헤어진 사이예요']),scene('timebridge','함께한 시간도\n들려주세요','시간이 흐르며 달라진 마음이 있을까요?'),choice('duration','서로 알고 지낸 기간은 얼마나 되나요?',['3개월 미만','3~6개월','6개월~1년','1~3년','3년 이상'],true),scene('infobridge','이제 두 분을\n차례로 알아갈게요','먼저 당신의 정보를 알려주세요.','내 정보 입력하기'),info,partner,{...question,title:'둘 사이에 궁금한 점이 있나요?'},sales,checkout],
compatibility:[intro('우리의 인연은\n어디로 향할까요','두 사람의 다음 장을 찾아가는 작은 여행.'),scene('guide','함께 걸어가요','마음이 향하는 사람을 떠올려 보세요.'),scene('train','잠시, 마음을\n쉬어가는 시간','지금부터 두 사람의 이야기에 집중해요.'),choice('greeting','어떤 마음으로 찾아왔나요?',['우리의 다름을 이해하고 싶어요','앞으로의 관계가 궁금해요']),scene('bond','두 사람을 잇는\n이야기를 펼쳐요','정답보다 서로를 이해하는 실마리를 찾아보세요.','우리 이야기 들려주기'),info,partner,choice('status','두 사람은 어떤 사이인가요?',['연애 중','짝사랑','썸','결혼','헤어진 관계']),choice('duration','함께한 시간은 얼마나 되나요?',['3개월 미만','3~6개월','6개월~2년','2년 이상']),{...question,title:'우리 사이, 무엇이 가장 궁금한가요?'},sales,checkout],
career:[intro('나에게 맞는 일,\n다음 선택의 방향','처음 시작하는 마음도, 다시 시작하는 용기도.'),scene('lift','잠시 멈춰\n방향을 살펴봐요','계속 가는 것과 다른 길을 택하는 것 사이에서 고민하나요?'),scene('future','어떤 하루를\n살고 싶은가요','좋아하는 일, 잘하는 일, 오래 할 수 있는 일을 함께 생각해요.'),info,choice('concern','지금 가장 고민하는 것은 무엇인가요?',['첫 취업을 준비해요','이직을 고민해요','다시 일을 시작하고 싶어요','창업을 생각해요','지금 일이 맞는지 궁금해요']),scene('drawer','나의 가능성을\n하나씩 꺼내요','강점과 일하는 방식, 나에게 필요한 환경을 살펴봐요.'),scene('chart','지금의 선택이\n다음 장으로 이어지도록','속도보다 중요한 건 나에게 맞는 방향일 수 있어요.'),scene('window','마지막 질문을\n남겨주세요','당신이 생각하는 다음 선택을 들려주세요.'),{...question,title:'직업에 관해 꼭 묻고 싶은 것이 있나요?'},checkout],
wealth:[intro('내 삶의 결실은\n언제 익어갈까요','모으는 방식도, 쓰는 기준도 사람마다 달라요.'),scene('tree','열매마다\n익는 때가 있어요','나의 리듬을 이해하는 일부터 시작해요.'),scene('others','다른 사람의 속도에\n마음을 빼앗기지 마세요','지금까지 쌓아온 것들을 먼저 돌아봐요.'),scene('timing','나에게 맞는\n결실의 방식을 찾아요','일과 돈을 대하는 태도, 반복되는 습관을 살펴봐요.'),scene('ask','당신의 이야기를\n들려주세요','태어난 날부터 천천히 시작해요.','내 정보 입력하기'),info,choice('occupation','현재 어떤 상황에 가까운가요?',['직장에 다니고 있어요','프리랜서로 일하고 있어요','사업을 운영하고 있어요','언제 나아질지 궁금해요','잠시 쉬고 있어요'],true),checkout]
};

// New catalog entries use the existing story, form, sales and checkout components.
FLOWS.business=[
 intro('내가 키우는 일의\n다음 장을 펼쳐요','시작을 준비하는 마음도, 오래 이어가고 싶은 마음도 들려주세요.'),
 scene('plan','사업의 방향을\n함께 돌아볼까요','무엇을 키우고 싶은지, 나에게 중요한 기준부터 살펴봐요.'),
 info,
 choice('stage','지금 사업의 어느 단계에 있나요?',['창업을 준비하고 있어요','처음 사업을 시작했어요','사업을 운영하고 있어요','새로운 확장을 고민해요','방향을 다시 정리하고 싶어요'],true),
 choice('priority','어떤 이야기를 먼저 살펴볼까요?',['나에게 맞는 사업 방식','함께 일하는 사람과의 호흡','운영과 확장 사이의 선택','나만의 강점을 찾는 일','지금의 계획을 돌아보는 일'],true),
 scene('direction','나만의 기준이\n사업의 중심이 되도록','일하는 성향과 지금의 상황을 나란히 놓고 생각해요.'),
 {...question,title:'사업에 관해 남기고 싶은 이야기가 있나요?',text:'준비하거나 운영 중인 일과 현재 고민을 편하게 적어주세요.'},
 scene('ready','당신의 사업 이야기를\n한 권으로 모았어요','지금의 계획을 돌아보고 다음 질문을 찾아보세요.','사업운 리포트 살펴보기'),
 sales,checkout
];
FLOWS.health=[
 intro('나의 몸과 마음에\n귀 기울이는 시간','요즘의 생활 리듬과 나를 돌보는 습관을 천천히 돌아봐요.'),
 scene('pause','잠시 숨을 고르고\n내 이야기를 들어봐요','일과 휴식 사이에서 나에게 필요한 시간을 떠올려 보세요.'),
 info,
 choice('rhythm','요즘 일상의 리듬은 어떤가요?',['대체로 규칙적으로 지내요','일정이 자주 바뀌어요','일과 휴식의 균형이 아쉬워요','나를 돌보는 시간을 늘리고 싶어요','아직 잘 모르겠어요'],true),
 choice('focus','어떤 생활 습관을 돌아보고 싶나요?',['잠들고 일어나는 리듬','스트레스와 쉬어가는 시간','활동과 휴식의 균형','꾸준히 이어갈 돌봄 습관','지금의 일상 전반'],true),
 scene('balance','나를 돌보는 일에도\n나만의 리듬이 있어요','사주를 통해 성향을 재미로 읽고, 직접 들려준 생활 습관을 돌아봐요.'),
 {...question,title:'나의 일상에 관해 더 들려줄 이야기가 있나요?',text:'바꾸고 싶은 생활 습관이나 일과 휴식에 관한 생각을 적어주세요. 비워두셔도 괜찮아요.'},
 scene('ready','나를 돌보는 질문을\n한 권에 담았어요','생활 리듬과 작은 실천을 돌아보는 건강운 이야기예요.','건강운 리포트 살펴보기'),
 sales,checkout
];

// SCOPE-01 / INPUT-01/02 / INTAKE-C01..06 / ISSUE-01.
const INTAKE_POLICY_VERSION='kr-c-2026-10-10.2';
function intakePayload(productId,draft={}){
 const person=v=>{if(!v||typeof v!=='object')return {};const keys=['name','birth','calendar','leap','leapStatus','timeAccuracy','time','unknown','timeRange','birthPlace','sex'];return Object.fromEntries(keys.filter(k=>v[k]!==undefined).map(k=>[k,v[k]]));};
 return {productId,self:person(draft.self),partner:person(draft.partner),answers:draft.answers||{},question:typeof draft.question==='string'?draft.question.slice(0,1000):''};
}
function evaluateIntake(payload={},trusted={}){
 const product=PRODUCTS.find(p=>p.id===payload.productId),pair=['reunion','intimate'].includes(payload.productId);
 const outcome=(status,code,message,extra={})=>({policyVersion:INTAKE_POLICY_VERSION,status,code,message,inputAccepted:false,paymentAllowed:false,issuanceAllowed:false,requiresHumanReview:false,requiresAutomatedValidation:true,...extra});
 if(!product)return outcome('blocked','UNKNOWN_PRODUCT','현재 판매 중인 상품을 선택해주세요.');
 if(pair&&!payload.partner?.birth)return outcome('blocked','PARTNER_BIRTH_REQUIRED','두 사람의 분석에는 상대방 생년월일이 필요해요. 확인 전에는 이 상품을 구매할 수 없어요.',{person:'partner'});
 const inputs={};const uncertainties=[];
 for(const who of pair?['self','partner']:['self']){
  const p=payload[who]||{};const label=who==='self'?'나의':'상대방의';
  if(p.birthPlace?.countryCode&&p.birthPlace.countryCode!=='KR')return outcome('blocked','UNSUPPORTED_COUNTRY',`${label} 출생 국가를 확인해주세요. 현재 대한민국 출생만 지원해요.`,{person:who});
  const date=validateBirthDate(p);
  if(!date.valid)return outcome(date.code==='DATE_UNCONFIRMED'?'needs_confirmation':'blocked',date.code||'INVALID_BIRTH_DATE',`${label} ${date.message}`,{person:who});
  if(!birthPlaceValid(p.birthPlace))return outcome('needs_confirmation','PLACE_REQUIRED',`${label} 국내 출생 지역을 선택하거나 모름으로 표시해주세요.`,{person:who});
  const timeError=birthRangeError(p);
  if(timeError)return outcome('needs_confirmation','TIME_REQUIRED',`${label} ${timeError}`,{person:who});
  if(!personValid(p))return outcome('needs_confirmation','PERSON_REQUIRED',`${label} 이름과 성별을 확인해주세요.`,{person:who});
  if(birthPrecision(p)!=='exact')uncertainties.push({person:who,kind:'time',message:`${label} 가능한 출생 시간 전체에서 공통 풀이와 달라지는 풀이를 확인해야 해요.`});
  if(p.birthPlace.status!=='known'||p.birthPlace.inputMode==='manual')uncertainties.push({person:who,kind:'place',message:`${label} 출생 지역에 따른 결과 차이를 확인해야 해요.`});
  inputs[who]=birthAnalysisInput(p);
 }
 for(const step of FLOWS[product.id].filter(s=>s.type==='choice')){
  const answer=payload.answers?.[step.id];
  if((step.required&&!answer)||(answer&&!step.options.includes(answer)))return outcome('needs_confirmation','QUESTION_REQUIRED','상품의 질문에 알맞은 답변을 선택해주세요.',{stepId:step.id});
 }
 const info={inputAccepted:true,analysisInputs:inputs,uncertainties,productId:product.id,priceKrw:product.price};
 // Coverage must be supplied by the trusted server adapter, bound to this exact input.
 const a=trusted.assessment;
 if(!a||!trusted.inputFingerprint||a.inputFingerprint!==trusted.inputFingerprint||a.policyVersion!==INTAKE_POLICY_VERSION)return outcome('awaiting_analysis','ANALYSIS_REQUIRED','입력은 확인했어요. 제공 가능한 풀이 범위의 검증이 끝난 뒤 구매할 수 있어요. 아직 결제나 주문은 생성되지 않았어요.',info);
 if(a.summary)info.analysisSummary=a.summary;
 if(a.calculationConflict!==false)return outcome('needs_review','CALCULATION_CONFLICT','계산 기준에 따른 결과 차이를 확인 중이에요. 확인 전에는 결제나 결과 발행을 진행하지 않아요.',info);
 if(a.coreCoverage!=='complete')return outcome('blocked','CORE_COVERAGE_INCOMPLETE',a.summary?.calculated?'명식 후보와 일부 구조 조건을 계산했어요. 이 상품의 전체 풀이 규칙과 자동 검증이 준비되기 전에는 구매할 수 없어요.':'현재 정보로는 이 상품의 핵심 분석을 제공할 수 없어 구매를 진행할 수 없어요.',info);
 if(uncertainties.length&&a.allPossibleVariantsEvaluated!==true)return outcome('needs_review','VARIANT_REVIEW_REQUIRED','불확실한 시간과 지역의 가능성을 모두 비교한 뒤 구매 가능 여부를 안내할게요.',info);
 if(!Array.isArray(a.disclosures)||a.disclosures.some(x=>typeof x!=='string')||(uncertainties.length&&!a.disclosures.length))return outcome('needs_review','DISCLOSURES_REQUIRED','제외되는 풀이와 달라지는 내용을 먼저 확인해야 해요.',info);
 if(!a.calculationVersion||!a.coverageVersion)return outcome('needs_review','EVIDENCE_REQUIRED','계산과 분석 범위의 검증 기록을 확인 중이에요.',info);
 return outcome('eligible','CORE_COVERAGE_CONFIRMED','상품의 핵심 분석을 제공할 수 있어요. 안내된 제한 사항을 확인해주세요.',{...info,paymentAllowed:true,disclosures:a.disclosures});
}


export {INTAKE_POLICY_VERSION,PRODUCTS,FLOWS,intakePayload,evaluateIntake,personValid,birthPrecision};
