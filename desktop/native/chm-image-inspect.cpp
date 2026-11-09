#include <opencv2/core.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>
#include <string>
#include <vector>

static void usage() {
    std::cout << "Usage: chm-image-inspect IMAGE [--json] [--edges OUTPUT] "
                 "[--grayscale OUTPUT] [--resize WIDTHxHEIGHT OUTPUT]\n"
                 "       chm-image-inspect --self-test | --help\n";
}
static bool to_gray(const cv::Mat& input, cv::Mat& gray) {
    if (input.channels() == 1) { gray = input; return true; }
    if (input.channels() == 3) { cv::cvtColor(input, gray, cv::COLOR_BGR2GRAY); return true; }
    if (input.channels() == 4) { cv::cvtColor(input, gray, cv::COLOR_BGRA2GRAY); return true; }
    return false;
}
static int self_test() {
    cv::Mat sample(32, 48, CV_8UC3);
    for (int y = 0; y < sample.rows; ++y)
        for (int x = 0; x < sample.cols; ++x)
            sample.at<cv::Vec3b>(y, x) = cv::Vec3b(
                static_cast<unsigned char>(x * 5),
                static_cast<unsigned char>(y * 7),
                static_cast<unsigned char>((x + y) * 3));
    std::vector<unsigned char> encoded;
    if (!cv::imencode(".png", sample, encoded) || encoded.empty()) return 2;
    const cv::Mat decoded = cv::imdecode(encoded, cv::IMREAD_UNCHANGED);
    if (decoded.empty() || decoded.size() != sample.size() || decoded.channels() != 3) return 3;
    cv::Mat gray, edges, resized;
    if (!to_gray(decoded, gray)) return 4;
    cv::Canny(gray, edges, 60.0, 150.0);
    cv::resize(decoded, resized, cv::Size(24, 16), 0.0, 0.0, cv::INTER_AREA);
    if (gray.empty() || edges.empty() || resized.size() != cv::Size(24, 16)) return 5;
    std::cout << "OpenCV " << CV_VERSION
              << " decode/encode/grayscale/Canny/resize self-test: PASS\n";
    return 0;
}
int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--self-test") return self_test();
    if (argc == 2 && (std::string(argv[1]) == "--help" || std::string(argv[1]) == "-h")) {
        usage(); return 0;
    }
    if (argc < 2) { usage(); return 64; }
    const std::string input_path = argv[1];
    const cv::Mat image = cv::imread(input_path, cv::IMREAD_UNCHANGED);
    if (image.empty()) { std::cerr << "Cannot decode image: " << input_path << "\n"; return 2; }
    bool json = false;
    for (int i = 2; i < argc; ++i) {
        const std::string option = argv[i];
        if (option == "--json") json = true;
        else if (option == "--edges" || option == "--grayscale") {
            if (i + 1 >= argc) { usage(); return 64; }
            const std::string output = argv[++i];
            cv::Mat gray, result;
            if (!to_gray(image, gray)) { std::cerr << "Unsupported channel count\n"; return 65; }
            if (option == "--edges") cv::Canny(gray, result, 100.0, 200.0);
            else result = gray;
            if (!cv::imwrite(output, result)) { std::cerr << "Cannot write: " << output << "\n"; return 3; }
        } else if (option == "--resize") {
            if (i + 2 >= argc) { usage(); return 64; }
            const std::string dimensions = argv[++i], output = argv[++i];
            const auto split = dimensions.find('x');
            if (split == std::string::npos) { usage(); return 64; }
            int width = 0, height = 0;
            try { width = std::stoi(dimensions.substr(0, split)); height = std::stoi(dimensions.substr(split + 1)); }
            catch (...) { usage(); return 64; }
            if (width < 1 || height < 1 || width > 16384 || height > 16384) {
                std::cerr << "Resize dimensions must be 1..16384\n"; return 64;
            }
            cv::Mat resized;
            cv::resize(image, resized, cv::Size(width, height), 0.0, 0.0, cv::INTER_AREA);
            if (!cv::imwrite(output, resized)) { std::cerr << "Cannot write: " << output << "\n"; return 3; }
        } else { std::cerr << "Unknown option: " << option << "\n"; usage(); return 64; }
    }
    const cv::Scalar mean = cv::mean(image);
    if (json) {
        std::cout << "{\"width\":" << image.cols << ",\"height\":" << image.rows
                  << ",\"channels\":" << image.channels() << ",\"depth\":" << image.depth()
                  << ",\"mean\":[" << mean[0] << "," << mean[1] << "," << mean[2] << "," << mean[3] << "]}\n";
    } else {
        std::cout << "file: " << input_path << "\nwidth: " << image.cols << "\nheight: " << image.rows
                  << "\nchannels: " << image.channels() << "\ndepth: " << image.depth()
                  << "\nmean: " << mean[0] << ", " << mean[1] << ", " << mean[2] << ", " << mean[3] << "\n";
    }
    return 0;
}
