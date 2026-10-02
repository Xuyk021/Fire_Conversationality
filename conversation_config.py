# conversation_config.py

CONVERSATIONS = {
    "neutral": {
        "introduction": "Hi, I’m Maya, a virtual preparedness assistant for the Florida Division of Emergency Management. I’m here to help you think through a few important steps to prepare for a hurricane. We’ll focus on practical things you can do ahead of time.",

        "rounds": [
            {
                "id": "alerts_and_risk",
                "label": "1. Alerts and Risk",
                "prompt": "In Florida, follow official updates from the National Hurricane Center, National Weather Service, Florida emergency management, and your local officials. Have you signed up for AlertFlorida?",
            },
            {
                "id": "evacuation",
                "label": "2. Evacuation",
                "prompt": "If local officials issue an evacuation order, follow their instructions. It helps to decide in advance where you would go and to have more than one possible route in case of traffic, flooding, or road closures. If you needed to evacuate, where would you most likely go?",
            },
            {
                "id": "emergency_supplies",
                "label": "3. Emergency Supplies",
                "prompt": "A good goal is to have at least seven days of essential supplies, including water, nonperishable food, medications, batteries, and anything needed by children or pets. What essential item would be hardest for your household to go without?",
            },
            {
                "id": "home_and_documents",
                "label": "4. Home and Documents",
                "prompt": "Before a hurricane, secure outdoor items and protect important identification, insurance, financial, and medical documents. It is also useful to keep photos or a video inventory of your belongings. Which of these tasks still needs your attention?",
            },
            {
                "id": "household_needs",
                "label": "5. Household Needs",
                "prompt": "Make sure your household knows how to stay in contact and where to meet if separated. Include medications, pets, transportation, mobility needs, and backup power for essential medical equipment in your plan. Is there anyone in your household who might need extra support during an evacuation or power outage?",
            },
        ],

        "closing": "You have now thought through the key parts of hurricane preparation: alerts, evacuation, supplies, protecting your home and documents, and your household’s specific needs. Preparing these things ahead of time can make it easier to act when a storm approaches.",
    },

    "empathic": {
        "introduction": "Hi, I’m Maya, a virtual preparedness assistant for the Florida Division of Emergency Management. I’m here to help you think through a few important steps to prepare for a hurricane. I understand that preparing for a hurricane can feel stressful or overwhelming, especially when you are unsure how a storm may affect you. We’ll focus on a few practical things you can do ahead of time.",

        "rounds": [
            # {
            #     "id": "alerts_and_risk",
            #     "label": "1. Alerts and Risk",
            #     "prompt": "I understand that it can be difficult to know when a storm is becoming serious enough to take action. In Florida, it is important to follow official updates from the National Hurricane Center, National Weather Service, Florida emergency management, and your local officials. A hurricane watch means hurricane conditions are possible; a warning means they are expected. It is also important to know your evacuation zone. Do you already know your evacuation zone and how you would receive local emergency alerts?",
            # },
            {
                "id": "evacuation",
                "label": "2. Evacuation",
                "prompt": "I can imagine that thinking about leaving your home can be stressful, especially when you do not know exactly what conditions will be like. If local officials issue an evacuation order, follow their instructions. It helps to decide in advance where you would go and to have more than one possible route in case of traffic, flooding, or road closures. If you needed to evacuate, where would you most likely go?",
            },
            {
                "id": "emergency_supplies",
                "label": "3. Emergency Supplies",
                "prompt": "I can see how preparing enough supplies for several days could feel like a lot to organize. A good goal is to have at least seven days of essential supplies, including water, nonperishable food, medications, batteries, and anything needed by children or pets. What essential item would be hardest for your household to go without?",
            },
            {
                "id": "home_and_documents",
                "label": "4. Home and Documents",
                "prompt": "I understand that preparing your home can take extra time and effort when you already have other responsibilities. Before a hurricane, secure outdoor items and protect important identification, insurance, financial, and medical documents. It is also useful to keep photos or a video inventory of your belongings. Which of these tasks still needs your attention?",
            },
            {
                "id": "household_needs",
                "label": "5. Household Needs",
                "prompt": "I can imagine that preparing becomes more complicated when you are also responsible for children, pets, older adults, or someone with medical or mobility needs. Make sure your household knows how to stay in contact and where to meet if separated. Include medications, pets, transportation, mobility needs, and backup power for essential medical equipment in your plan. Is there anyone in your household who might need extra support during an evacuation or power outage?",
            },
        ],

        "closing": "You have now thought through the key parts of hurricane preparation: alerts, evacuation, supplies, protecting your home and documents, and your household’s specific needs. I understand that getting ready for a hurricane can feel demanding, but preparing these things ahead of time can make it easier to act when a storm approaches.",
    },
}