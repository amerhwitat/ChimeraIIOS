#include <opencv2/core.hpp>
#include <opencv2/imgcodecs.hpp>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--self-test") {
        cv::Mat sample(8, 12, CV_8UC3, cv::Scalar(10, 20, 30));
        if (sample.empty() || sample.rows != 8 || sample.cols != 12 || sample.channels() != 3) return 2;
        std::cout << "OpenCV " << CV_VERSION << " self-test: PASS\n";
        return 0;
    }
    if (argc != 2) {
        std::cerr << "Usage: chm-image-inspect IMAGE | --self-test\n";
        return 64;
    }
    const cv::Mat image = cv::imread(argv[1], cv::IMREAD_UNCHANGED);
    if (image.empty()) {
        std::cerr << "Cannot decode image: " << argv[1] << "\n";
        return 2;
    }
    const cv::Scalar mean = cv::mean(image);
    std::cout << "file: " << argv[1] << "\n"
              << "width: " << image.cols << "\n"
              << "height: " << image.rows << "\n"
              << "channels: " << image.channels() << "\n"
              << "depth: " << image.depth() << "\n"
              << "mean: " << mean[0] << ", " << mean[1] << ", " << mean[2] << ", " << mean[3] << "\n";
    return 0;
}
