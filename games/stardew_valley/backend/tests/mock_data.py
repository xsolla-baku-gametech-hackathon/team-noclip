# Mock GameStateDto payloads for testing and demonstration

MOCK_GAME_STATE = {
    "player": {
        "name": "Aykhan",
        "farmName": "Misty Farm",
        "gold": 12450
    },
    "date": {
        "season": "Summer",
        "day": 18,
        "year": 2,
        "timeOfDay": 930
    },
    "farm": {
        "cropCount": 47,
        "readyToHarvest": 8,
        "needsWater": 12,
        "deadCrops": 2
    },
    "crops": [
        {"cropName": "Blueberry", "state": "ready", "x": 12, "y": 18},
        {"cropName": "Melon", "state": "needs_water", "x": 14, "y": 18},
        {"cropName": "Wheat", "state": "dead", "x": 15, "y": 18}
    ],
    "communityCenter": {
        "complete": False,
        "completedBundles": 18,
        "totalBundles": 30,
        "missingItems": ["Red Cabbage", "Truffle", "Rabbit's Foot"]
    },
    "activeQuests": [
        {
            "title": "Robin's Request",
            "description": "Bring Robin 10 Hardwood.",
            "daysLeft": 2,
            "isSpecialOrder": False
        },
        {
            "title": "Delivery to Clint",
            "description": "Bring Clint 1 Copper Bar.",
            "daysLeft": 0,
            "isSpecialOrder": False
        }
    ],
    "social": {
        "lowHeartVillagers": [
            {"name": "Penny", "hearts": 2, "birthday": "Fall 2"}
        ],
        "upcomingBirthdays": [
            {"name": "Demetrius", "hearts": 5, "birthday": "Summer 19"}
        ]
    }
}

SAMPLE_STARDEW_XML = """<?xml version="1.0" encoding="utf-8"?>
<SaveGame xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <player>
    <name>Aykhan</name>
    <farmName>Misty Farm</farmName>
    <money>12450</money>
    <friendshipData>
      <item>
        <key><string>Penny</string></key>
        <value><Friendship><Points>500</Points></Friendship></value>
      </item>
    </friendshipData>
  </player>
  <currentSeason>Summer</currentSeason>
  <dayOfMonth>18</dayOfMonth>
  <year>2</year>
  <timeOfDay>930</timeOfDay>
  <hasCompletedCommunityCenter>false</hasCompletedCommunityCenter>
  <questLog>
    <Quest>
      <_questTitle>Robin's Request</_questTitle>
      <questDescription>Bring Robin 10 Hardwood.</questDescription>
      <daysLeft>2</daysLeft>
    </Quest>
  </questLog>
  <locations>
    <GameLocation xsi:type="Farm">
      <name>Farm</name>
      <terrainFeatures>
        <item>
          <key><Vector2><X>12</X><Y>18</Y></Vector2></key>
          <value>
            <TerrainFeature xsi:type="HoeDirt">
              <state>0</state>
              <crop>
                <indexOfHarvest>258</indexOfHarvest>
                <currentPhase>4</currentPhase>
                <dead>false</dead>
                <phaseDays><int>1</int><int>2</int><int>3</int><int>4</int></phaseDays>
              </crop>
            </TerrainFeature>
          </value>
        </item>
      </terrainFeatures>
    </GameLocation>
  </locations>
</SaveGame>
"""
