class Logger {
public:
    static Logger& Instance() {
        static Logger instance;
        return instance;
    }

    void Log(const std::string& message, LogLevel level = LogLevel::INFO) {
        std::lock_guard<std::mutex> lock(logMutex);
        auto now = std::chrono::system_clock::now();
        auto timestamp = std::chrono::system_clock::to_time_t(now);

        std::stringstream ss;
        ss << "[" << std::put_time(std::localtime(&timestamp), "%Y-%m-%d %H:%M:%S") << "] "
           << LevelToString(level) << ": " << message;

        std::cout << ss.str() << std::endl;
        
        std::ofstream logFile("spoofer.log", std::ios::app);
        if (logFile.is_open()) {
            logFile << ss.str() << std::endl;
        }
    }

private:
    enum class LogLevel { DEBUG, INFO, WARNING, ERROR };
    std::mutex logMutex;
};