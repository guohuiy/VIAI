//#include <iostream>
//#include<vector>
//
//using namespace std;
//
//int test() {
//    // int a, b;
//    // while (cin >> a >> b) { // 注意 while 处理多个 case
//    //     cout << a + b << endl;
//    // }
//    vector<int> val(13, 4);
//    string s1, s2;
//    cin >> s1 >> s2;
//	s1 = s1 + "-" + s2;
//    for (int i = s1.size() - 1; i >= 0; --i) {
//        if (s1[i] == '-' || s1[i] == 'B' || s1[i] == 'C') continue;
//        else if (s1[i] == 'J') --val[10];
//        else if (s1[i] == 'Q') --val[11];
//        else if (s1[i] == 'K') --val[12];
//        else if (s1[i] == 'A') --val[0];
//        else if (s1[i] == '0') { 
//            --i; --val[9];
//        }
//        else --val[(s1[i] - '0') - 1];
//    }
//    /*for (int i = s2.size() - 1; i >= 0; --i) {
//        if (s1[i] == '-') continue;
//        else if (s2[i] == 'J') --val[10];
//        else if (s2[i] == 'Q') --val[11];
//        else if (s2[i] == 'K') --val[12];
//        else if (s1[i] != 'B' && s1[i] != 'C') --val[(s1[i] - '0') - 1];
//    }*/
//
//    int len1 = 0, pos1 = -1, len2 = 0, pos2 = -1;
//    if (val[0] > 0) {
//        len1 += 1;
//        pos1 = 0;
//        for (int j = 12; j > 1; --j) {
//            if (val[j] > 0) ++len1;
//            else break;
//        }
//        if (len1 < 5) {
//            len1 = 0;
//            pos1 = -1;
//        }
//
//    }
//    for (int i = 12; i >= 4; --i) {
//        pos2 = i;
//        for (int j = i; j > 1; --j) {
//            if (val[j] > 0) ++len2;
//            else break;
//        }
//        if (len2 >= 5) {
//            if (len2 > len1 || len1 == 0) {
//                pos1 = pos2;
//                len1 = len2;
//            }
//        }
//        pos2 = -1;
//        len2 = 0;
//    }
//
//    if (pos1 < 0) cout << "NO-CHAIN" << endl;
//    else {
//        if (pos1 == 0) {
//            for (int i = 0; i < len1 - 4; ++i) cout << 10 - (len1 - 4) + 1 +i << "-";
//            cout << "J-Q-K-A" << endl;
//        }
//        else {
//            for (int i = pos1 - len1 + 1; i <= pos1; ++i) {
//                if (pos1 < 10) {
//                    if (i != pos1)cout << i + 1 << '-';
//                    else cout << i + 1 << endl;
//                }
//                else {
//                    if (i < 10) cout << i + 1 << '-';
//                    else {
//                        switch (pos1 - 9) {
//                        case 1: { cout << 'J' << endl; break; }
//                        case 2: {cout << "J-Q" << endl; break;}
//                        case 3: { cout << "J-Q-K" << endl; break; }
//                        }
//                        break;
//                    }
//                }
//            }
//        }
//    }
//
//	return 0;
//}
//
//int main() {
//    int n = 1000;
//    cout << (1 << 7)-1 << endl;
//    return 0;
//}
//// 64 位输出请用 printf("%lld")
#include "opencv2/opencv.hpp"
#include <iostream>

int main() {
    cv::Mat img = cv::Mat::zeros(100, 100, CV_8UC3);
    std::cout << "OpenCV version: " << CV_VERSION << std::endl;
    std::cout << "Test image size: " << img.rows << "x" << img.cols << std::endl;
    return 0;
}