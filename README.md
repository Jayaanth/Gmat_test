flowchart TD
    subgraph Frontend["Frontend Interface"]
        UI[/"User Interface\nReact Components"/]
        StartBtn["Start Test Button"]
        QuestionDisplay["Question Display"]
        AnswerInput["Answer Input"]
        Progress["Progress Tracker"]
        Results["Results Display"]
    end

    subgraph TestEngine["Test Engine"]
        QM["Question Manager"]
        DifficultyAdapter["Difficulty Adapter"]
        ScoreCalculator["Score Calculator"]
        SessionManager["Session Manager"]
    end

    subgraph AIServices["AI Services"]
        QG["Question Generator\nAI Model"]
        DE["Difficulty Evaluator\nAI Model"]
    end

    subgraph DataStore["Data Management"]
        TestSession["Session Storage"]
        QuestionBank["Question Bank"]
        UserProgress["Progress Tracker"]
        ScoreHistory["Score History"]
    end

    %% Frontend Interactions
    StartBtn --> SessionManager
    SessionManager --> QM
    QM --> QuestionDisplay
    AnswerInput --> SessionManager
    SessionManager --> Progress
    SessionManager --> Results

    %% Test Engine Logic
    QM <--> QG
    QM <--> QuestionBank
    SessionManager <--> DifficultyAdapter
    DifficultyAdapter <--> DE
    SessionManager <--> ScoreCalculator
    
    %% Data Flow
    SessionManager <--> TestSession
    SessionManager <--> UserProgress
    ScoreCalculator --> ScoreHistory

    %% State Updates
    TestSession --> Results
    UserProgress --> Progress

    classDef frontend fill:#d4f1f4,stroke:#333,stroke-width:1px
    classDef engine fill:#ffed99,stroke:#333,stroke-width:1px
    classDef ai fill:#e8c2ca,stroke:#333,stroke-width:1px
    classDef data fill:#b1e693,stroke:#333,stroke-width:1px

    class UI,StartBtn,QuestionDisplay,AnswerInput,Progress,Results frontend
    class QM,DifficultyAdapter,ScoreCalculator,SessionManager engine
    class QG,DE ai
    class TestSession,QuestionBank,UserProgress,ScoreHistory data