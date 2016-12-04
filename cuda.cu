#include<iostream>
#include<cstdio>

using namespace std;

__global__ void printDevice() {
	int x;
	x = threadIdx.x;
	printf(" Thread %d says Hello\n", x);
}

int main()  {
	printDevice<<<2,10>>>();
}
